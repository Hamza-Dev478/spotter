"""Pure-domain geographic value objects (no framework dependencies)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatLng:
    """An immutable WGS84 coordinate."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError(f"latitude out of range: {self.lat}")
        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError(f"longitude out of range: {self.lon}")

    def as_lon_lat(self) -> tuple[float, float]:
        """OSRM and GeoJSON order coordinates as (lon, lat)."""
        return (self.lon, self.lat)


@dataclass(frozen=True)
class Location:
    """A resolved place: the address the user typed plus its geocoded point."""

    query: str
    label: str
    point: LatLng
