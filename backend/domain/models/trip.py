"""Pure-domain trip & route value objects (no framework dependencies)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .location import LatLng, Location


class StopType(str, Enum):
    START = "start"
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    FUEL = "fuel"
    REST = "rest"


@dataclass(frozen=True)
class RouteLeg:
    """A single driven leg as returned by the routing provider."""

    origin: LatLng
    destination: LatLng
    distance_miles: float
    drive_hours: float
    geometry: list[tuple[float, float]]  # ordered (lon, lat) points

    @property
    def avg_speed_mph(self) -> float:
        """Effective speed implied by the routing provider for this leg."""
        if self.drive_hours <= 0:
            return 0.0
        return self.distance_miles / self.drive_hours


@dataclass(frozen=True)
class RouteStop:
    """A point of interest placed on the route for the map markers."""

    type: StopType
    label: str
    point: LatLng
    at_mile: float


@dataclass(frozen=True)
class Route:
    """The full planned route: ordered legs + a merged geometry."""

    legs: list[RouteLeg]
    geometry: list[tuple[float, float]]  # merged (lon, lat) points

    @property
    def total_miles(self) -> float:
        return sum(leg.distance_miles for leg in self.legs)

    @property
    def total_drive_hours(self) -> float:
        return sum(leg.drive_hours for leg in self.legs)


@dataclass(frozen=True)
class Trip:
    """The user's request expressed in domain terms."""

    current: Location
    pickup: Location
    dropoff: Location
    current_cycle_used_hours: float
