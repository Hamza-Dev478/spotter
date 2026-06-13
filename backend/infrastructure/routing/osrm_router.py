"""Driving routes via the public OSRM demo server (keyless).

OSRM returns distance (metres), duration (seconds) and a GeoJSON LineString.
We request a *simplified* overview so the geometry payload stays small while
still tracing the road accurately enough for the map.
"""

from __future__ import annotations

import requests
from django.conf import settings

from application.errors import ProviderUnavailable, RoutingError
from application.interfaces.routing import IRoutingService
from domain.models.location import LatLng
from domain.models.trip import RouteLeg

from ..cache import get_or_compute, make_key

_METERS_PER_MILE = 1609.344


class OSRMRouter(IRoutingService):
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.OSRM_BASE_URL).rstrip("/")
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    def route(self, origin: LatLng, destination: LatLng) -> RouteLeg:
        key = make_key("route", origin.lat, origin.lon, destination.lat, destination.lon)
        leg = get_or_compute(key, lambda: self._fetch(origin, destination))
        if leg is None:
            raise RoutingError("No route found between the given points.")
        return leg

    # -- internal -----------------------------------------------------------
    def _fetch(self, origin: LatLng, destination: LatLng) -> RouteLeg | None:
        coords = f"{origin.lon},{origin.lat};{destination.lon},{destination.lat}"
        try:
            resp = requests.get(
                f"{self.base_url}/route/v1/driving/{coords}",
                params={"overview": "simplified", "geometries": "geojson"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderUnavailable(f"Routing provider error: {exc}") from exc

        routes = data.get("routes") or []
        if not routes:
            return None

        top = routes[0]
        geometry = [tuple(pt) for pt in top["geometry"]["coordinates"]]  # (lon, lat)
        return RouteLeg(
            origin=origin,
            destination=destination,
            distance_miles=top["distance"] / _METERS_PER_MILE,
            drive_hours=top["duration"] / 3600.0,
            geometry=geometry,
        )
