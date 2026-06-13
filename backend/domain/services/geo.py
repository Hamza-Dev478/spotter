"""Pure geometry helpers for placing markers along a route polyline."""

from __future__ import annotations

import math

# geometry points are (lon, lat) tuples, matching GeoJSON / OSRM order.
Point = tuple[float, float]

_EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(a: Point, b: Point) -> float:
    lon1, lat1 = a
    lon2, lat2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_RADIUS_MILES * math.asin(min(1.0, math.sqrt(h)))


def point_at_fraction(geometry: list[Point], fraction: float) -> Point | None:
    """Return the coordinate `fraction` (0..1) of the way along the polyline."""
    if not geometry:
        return None
    if len(geometry) == 1:
        return geometry[0]

    fraction = max(0.0, min(1.0, fraction))
    segment_lengths = [
        haversine_miles(geometry[i], geometry[i + 1]) for i in range(len(geometry) - 1)
    ]
    total = sum(segment_lengths)
    if total == 0:
        return geometry[0]

    target = fraction * total
    travelled = 0.0
    for i, length in enumerate(segment_lengths):
        if travelled + length >= target:
            ratio = (target - travelled) / length if length else 0.0
            lon1, lat1 = geometry[i]
            lon2, lat2 = geometry[i + 1]
            return (lon1 + (lon2 - lon1) * ratio, lat1 + (lat2 - lat1) * ratio)
        travelled += length
    return geometry[-1]
