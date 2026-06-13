"""Django ORM implementation of the trip repository."""

from __future__ import annotations

from application.interfaces.trip_repository import ITripRepository

from ..models import Trip


class DjangoTripRepository(ITripRepository):
    def save(self, request_payload: dict, result: dict) -> dict:
        summary = result.get("summary", {})
        trip = Trip.objects.create(
            current_location=request_payload.get("currentLocation", ""),
            pickup_location=request_payload.get("pickupLocation", ""),
            dropoff_location=request_payload.get("dropoffLocation", ""),
            current_cycle_used_hours=request_payload.get("currentCycleUsedHrs", 0) or 0,
            total_miles=summary.get("totalMiles", 0) or 0,
            total_drive_hours=summary.get("totalDriveHours", 0) or 0,
            days=len(result.get("dailyLogs", [])),
            request_payload=request_payload,
            result=result,
        )
        return self._summary(trip)

    def list_recent(self, limit: int = 10, offset: int = 0) -> list[dict]:
        return [self._summary(t) for t in Trip.objects.all()[offset : offset + limit]]

    def count(self) -> int:
        return Trip.objects.count()

    def get(self, trip_id: int) -> dict | None:
        trip = Trip.objects.filter(pk=trip_id).first()
        if trip is None:
            return None
        return {**self._summary(trip), "request": trip.request_payload, "result": trip.result}

    def delete(self, trip_id: int) -> bool:
        deleted, _ = Trip.objects.filter(pk=trip_id).delete()
        return deleted > 0

    def clear(self) -> None:
        Trip.objects.all().delete()

    @staticmethod
    def _summary(trip: Trip) -> dict:
        return {
            "id": trip.id,
            "createdAt": trip.created_at.isoformat().replace("+00:00", "Z"),
            "currentLocation": trip.current_location,
            "pickupLocation": trip.pickup_location,
            "dropoffLocation": trip.dropoff_location,
            "currentCycleUsedHrs": trip.current_cycle_used_hours,
            "totalMiles": round(trip.total_miles, 1),
            "totalDriveHours": round(trip.total_drive_hours, 2),
            "days": trip.days,
        }
