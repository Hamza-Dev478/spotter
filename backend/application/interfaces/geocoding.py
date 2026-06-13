"""Abstraction for geocoding providers (implemented in infrastructure)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.location import Location


class IGeocodingService(ABC):
    @abstractmethod
    def geocode(self, query: str) -> Location:
        """Resolve a free-text address to a single best-match Location.

        Raises:
            GeocodingError: if no match is found.
            ProviderUnavailable: if the provider errors or times out.
        """

    @abstractmethod
    def suggest(self, query: str, limit: int = 5) -> list[dict]:
        """Return up to `limit` autocomplete candidates: {label, lat, lon}."""

    @abstractmethod
    def reverse(self, lat: float, lon: float) -> str:
        """Reverse-geocode a coordinate to a short "City, ST" label.

        Best-effort: returns an empty string on failure (callers fall back to a
        generic label) so a reverse-geocode hiccup never fails trip planning.
        """
