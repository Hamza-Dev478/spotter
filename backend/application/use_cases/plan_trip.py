"""The PlanTrip use case: geocode -> route -> schedule HOS -> assemble output.

This is the orchestration layer. It depends only on abstractions (geocoder,
router) and pure domain services (scheduler, log builder, geo), never on Django
or a specific provider.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.models.hos import DutyStatus, Segment
from domain.models.location import LatLng, Location
from domain.models.trip import Route, RouteLeg, StopType
from domain.services.geo import point_at_fraction
from domain.services.hos_scheduler import HOSScheduler
from domain.services.log_builder import build_daily_logs

from application.dtos.plan_trip_input import PlanTripInput
from application.interfaces.geocoding import IGeocodingService
from application.interfaces.routing import IRoutingService

_REST_THRESHOLD_MIN = 10 * 60  # off-duty blocks >= 10h are drawn as rest stops


@dataclass
class PlanTripUseCase:
    geocoder: IGeocodingService
    router: IRoutingService
    scheduler: HOSScheduler
    fuel_interval_miles: float

    def execute(self, inp: PlanTripInput) -> dict:
        current = self.geocoder.geocode(inp.current_location)
        pickup = self.geocoder.geocode(inp.pickup_location)
        dropoff = self.geocoder.geocode(inp.dropoff_location)

        leg_a = self.router.route(current.point, pickup.point)
        leg_b = self.router.route(pickup.point, dropoff.point)
        route = Route(legs=[leg_a, leg_b], geometry=leg_a.geometry + leg_b.geometry)

        segments = self.scheduler.build_schedule(
            route, inp.start_time, inp.current_cycle_used_hours
        )

        # Reverse-geocode the change-of-duty locations to "City, ST" for the log
        # Remarks (FMCSA §395.8) and the map markers.
        start_place = self._place_for(current.point, current.label)
        pickup_place = self._place_for(pickup.point, pickup.label)
        dropoff_place = self._place_for(dropoff.point, dropoff.label)
        fuel_pts = self._fuel_points(route)
        rest_pts = self._rest_points(route, segments)

        self._enrich_segments(
            segments, start_place, pickup_place, dropoff_place,
            [p["place"] for p in fuel_pts], [p["place"] for p in rest_pts],
        )

        daily_logs = build_daily_logs(segments)
        stops = self._build_stops(
            current, pickup, dropoff, route,
            start_place, pickup_place, dropoff_place, fuel_pts, rest_pts,
        )

        return {
            "summary": self._summary(route, segments, stops, inp, len(daily_logs)),
            "route": {
                "geometry": {"type": "LineString", "coordinates": [list(p) for p in route.geometry]},
                "legs": [
                    self._leg("current", "pickup", leg_a),
                    self._leg("pickup", "dropoff", leg_b),
                ],
            },
            "stops": stops,
            "dailyLogs": daily_logs,
            "logMeta": dict(inp.log_meta or {}),
        }

    # -- place resolution ---------------------------------------------------
    def _place_for(self, point: LatLng, fallback_label: str) -> str:
        return self.geocoder.reverse(point.lat, point.lon) or _short(fallback_label)

    def _fuel_points(self, route: Route) -> list[dict]:
        total = route.total_miles or 1.0
        out: list[dict] = []
        mile = self.fuel_interval_miles
        while mile < route.total_miles:
            pt = point_at_fraction(route.geometry, mile / total)
            if pt:
                out.append({"atMile": mile, "lat": pt[1], "lon": pt[0], "place": self.geocoder.reverse(pt[1], pt[0])})
            mile += self.fuel_interval_miles
        return out

    def _rest_points(self, route: Route, segments: list[Segment]) -> list[dict]:
        total = route.total_miles or 1.0
        out: list[dict] = []
        cum = 0.0
        for seg in segments:
            if seg.duty_status == DutyStatus.DRIVING:
                cum += seg.miles
            elif seg.duty_status == DutyStatus.OFF_DUTY and seg.duration_minutes >= _REST_THRESHOLD_MIN:
                pt = point_at_fraction(route.geometry, min(cum / total, 1.0))
                kind = "34-hour restart" if seg.duration_minutes >= 34 * 60 else "10-hour rest"
                out.append({
                    "atMile": cum,
                    "lat": pt[1] if pt else 0.0,
                    "lon": pt[0] if pt else 0.0,
                    "place": self.geocoder.reverse(pt[1], pt[0]) if pt else "",
                    "kind": kind,
                })
        return out

    def _enrich_segments(
        self,
        segments: list[Segment],
        start_place: str,
        pickup_place: str,
        dropoff_place: str,
        fuel_places: list[str],
        rest_places: list[str],
    ) -> None:
        """Rewrite segment labels to include the City, ST of each duty change."""
        fuel_i = rest_i = 0
        first_drive = True
        for seg in segments:
            if seg.duty_status == DutyStatus.DRIVING:
                if first_drive and start_place:
                    seg.location_label = f"Began driving — {start_place}"
                    first_drive = False
            elif seg.duty_status == DutyStatus.ON_DUTY:
                if seg.location_label == "Pickup":
                    seg.location_label = _join("Pickup / loading", pickup_place)
                    seg.remark = ""
                elif seg.location_label == "Dropoff":
                    seg.location_label = _join("Dropoff / unloading", dropoff_place)
                    seg.remark = ""
                elif seg.location_label.startswith("Fuel"):
                    place = fuel_places[fuel_i] if fuel_i < len(fuel_places) else ""
                    fuel_i += 1
                    seg.location_label = _join("Fuel stop", place) or seg.location_label
                    seg.remark = ""
            elif seg.duty_status == DutyStatus.OFF_DUTY and seg.duration_minutes >= _REST_THRESHOLD_MIN:
                place = rest_places[rest_i] if rest_i < len(rest_places) else ""
                rest_i += 1
                base = "34-hour restart" if seg.duration_minutes >= 34 * 60 else "10-hour rest"
                seg.location_label = _join(base, place)
                seg.remark = ""

    # -- assembly -----------------------------------------------------------
    def _build_stops(
        self,
        current: Location,
        pickup: Location,
        dropoff: Location,
        route: Route,
        start_place: str,
        pickup_place: str,
        dropoff_place: str,
        fuel_pts: list[dict],
        rest_pts: list[dict],
    ) -> list[dict]:
        stops = [
            self._stop(StopType.START, start_place or current.label, current.point.lat, current.point.lon, 0.0),
            self._stop(StopType.PICKUP, pickup_place or pickup.label, pickup.point.lat, pickup.point.lon, route.legs[0].distance_miles),
            self._stop(StopType.DROPOFF, dropoff_place or dropoff.label, dropoff.point.lat, dropoff.point.lon, route.total_miles),
        ]
        for fp in fuel_pts:
            label = _join(f"Fuel stop (~{int(fp['atMile'])} mi)", fp["place"])
            stops.append(self._stop(StopType.FUEL, label, fp["lat"], fp["lon"], fp["atMile"]))
        for rp in rest_pts:
            stops.append(self._stop(StopType.REST, _join(rp["kind"], rp["place"]), rp["lat"], rp["lon"], rp["atMile"]))

        stops.sort(key=lambda s: s["atMile"])
        return stops

    def _summary(
        self,
        route: Route,
        segments: list[Segment],
        stops: list[dict],
        inp: PlanTripInput,
        days: int,
    ) -> dict:
        end = segments[-1].end_time if segments else inp.start_time
        duration_hours = (end - inp.start_time).total_seconds() / 3600.0
        return {
            "totalMiles": round(route.total_miles, 1),
            "totalDriveHours": round(route.total_drive_hours, 2),
            "totalDurationHours": round(duration_hours, 2),
            "fuelStops": sum(1 for s in stops if s["type"] == StopType.FUEL.value),
            "restStops": sum(1 for s in stops if s["type"] == StopType.REST.value),
            "days": days,
            "startTime": _iso(inp.start_time),
            "estimatedCompletionTime": _iso(end),
            "cycleHoursUsedAtEnd": round(self._cycle_at_end(segments, inp.current_cycle_used_hours), 2),
        }

    @staticmethod
    def _cycle_at_end(segments: list[Segment], initial: float) -> float:
        cycle = max(0.0, initial)
        for seg in segments:
            if seg.duty_status in (DutyStatus.DRIVING, DutyStatus.ON_DUTY):
                cycle += seg.duration_minutes / 60.0
            elif seg.duty_status == DutyStatus.OFF_DUTY and seg.duration_minutes >= 34 * 60:
                cycle = 0.0
        return cycle

    @staticmethod
    def _leg(origin: str, destination: str, leg: RouteLeg) -> dict:
        return {
            "from": origin,
            "to": destination,
            "distanceMiles": round(leg.distance_miles, 1),
            "durationHours": round(leg.drive_hours, 2),
        }

    @staticmethod
    def _stop(stop_type: StopType, label: str, lat: float, lon: float, at_mile: float) -> dict:
        return {
            "type": stop_type.value,
            "label": label,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "atMile": round(at_mile, 1),
        }


def _short(label: str) -> str:
    """Shorten a long Nominatim display_name to its first two comma parts."""
    parts = [p.strip() for p in (label or "").split(",") if p.strip()]
    return ", ".join(parts[:2]) if parts else (label or "")


def _join(base: str, place: str) -> str:
    return f"{base} — {place}" if place else base


def _iso(dt) -> str:
    return dt.isoformat().replace("+00:00", "Z")
