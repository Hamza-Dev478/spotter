"""Abstraction for routing providers (implemented in infrastructure)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.location import LatLng
from domain.models.trip import RouteLeg


class IRoutingService(ABC):
    @abstractmethod
    def route(self, origin: LatLng, destination: LatLng) -> RouteLeg:
        """Compute a single driving leg (distance, drive time, geometry).

        Raises:
            RoutingError: if no route exists.
            ProviderUnavailable: if the provider errors or times out.
        """
