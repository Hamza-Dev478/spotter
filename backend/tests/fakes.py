"""In-memory fakes implementing the application interfaces, for fast tests."""

from __future__ import annotations

from application.errors import GeocodingError
from application.interfaces.geocoding import IGeocodingService
from application.interfaces.routing import IRoutingService
from domain.models.location import LatLng, Location
from domain.models.trip import RouteLeg
from domain.services.geo import haversine_miles

# A few real city coordinates so routes have plausible distances.
_CITIES = {
    "chicago": (41.8781, -87.6298),
    "st louis": (38.6270, -90.1994),
    "dallas": (32.7767, -96.7970),
    "denver": (39.7392, -104.9903),
    "los angeles": (34.0522, -118.2437),
}


class FakeGeocoder(IGeocodingService):
    def __init__(self, fail_on: str | None = None) -> None:
        self.fail_on = fail_on

    def geocode(self, query: str) -> Location:
        key = query.strip().lower()
        if self.fail_on and self.fail_on.lower() in key:
            raise GeocodingError(f"Could not geocode: '{query}'")
        lat, lon = _CITIES.get(key, (40.0 + len(key) * 0.1, -90.0 - len(key) * 0.1))
        return Location(query=query, label=query.title(), point=LatLng(lat, lon))

    def suggest(self, query: str, limit: int = 5) -> list[dict]:
        return [{"label": query.title(), "lat": 40.0, "lon": -90.0}]

    def reverse(self, lat: float, lon: float) -> str:
        # Deterministic "City, ST" so tests can assert the format without HTTP.
        return f"Testville{abs(int(lat))}, TS"


class FakeRouter(IRoutingService):
    """Straight-line distance at a fixed ~55 mph, with a 2-point geometry."""

    def __init__(self, speed_mph: float = 55.0) -> None:
        self.speed_mph = speed_mph

    def route(self, origin: LatLng, destination: LatLng) -> RouteLeg:
        miles = haversine_miles(origin.as_lon_lat(), destination.as_lon_lat())
        return RouteLeg(
            origin=origin,
            destination=destination,
            distance_miles=miles,
            drive_hours=miles / self.speed_mph if self.speed_mph else 0.0,
            geometry=[origin.as_lon_lat(), destination.as_lon_lat()],
        )
