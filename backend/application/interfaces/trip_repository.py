"""Abstraction for trip persistence (implemented in infrastructure)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ITripRepository(ABC):
    @abstractmethod
    def save(self, request_payload: dict, result: dict) -> dict:
        """Persist a planned trip; return the stored record (id + created_at)."""

    @abstractmethod
    def list_recent(self, limit: int = 10, offset: int = 0) -> list[dict]:
        """Return a page of recent trips, newest first (summary fields only)."""

    @abstractmethod
    def count(self) -> int:
        """Total number of stored trips (for pagination)."""

    @abstractmethod
    def get(self, trip_id: int) -> dict | None:
        """Return the full stored trip (request + result) or None."""

    @abstractmethod
    def delete(self, trip_id: int) -> bool:
        """Delete one trip; return True if it existed."""

    @abstractmethod
    def clear(self) -> None:
        """Delete all stored trips."""
