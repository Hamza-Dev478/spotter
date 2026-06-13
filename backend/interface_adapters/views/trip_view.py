"""DRF views — the HTTP boundary. They translate requests into use-case calls
and map domain/application errors onto HTTP status codes."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from application.dtos.plan_trip_input import PlanTripInput
from application.errors import GeocodingError, ProviderUnavailable, RoutingError
from application.use_cases.plan_trip import PlanTripUseCase
from domain.services.hos_scheduler import HOSScheduler
from domain.models.hos import HOSConstants
from infrastructure import factory

from ..serializers.trip import TripInputSerializer


def _use_case() -> PlanTripUseCase:
    constants = HOSConstants(fuel_interval_miles=settings.FUEL_INTERVAL_MILES)
    return PlanTripUseCase(
        geocoder=factory.get_geocoder(),
        router=factory.get_router(),
        scheduler=HOSScheduler(constants),
        fuel_interval_miles=settings.FUEL_INTERVAL_MILES,
    )


class TripPlannerView(APIView):
    """POST /api/v1/trips/plan/ — plan a trip and persist it."""

    def post(self, request: Request) -> Response:
        serializer = TripInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        inp = PlanTripInput(
            current_location=data["currentLocation"],
            pickup_location=data["pickupLocation"],
            dropoff_location=data["dropoffLocation"],
            current_cycle_used_hours=data["currentCycleUsedHrs"],
            start_time=data.get("startTime") or timezone.now(),
            log_meta=dict(data.get("logMeta") or {}),
        )

        try:
            result = _use_case().execute(inp)
        except GeocodingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except (RoutingError, ProviderUnavailable) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        factory.get_trip_repository().save(request.data, result)
        return Response(result, status=status.HTTP_200_OK)


class GeocodeSuggestView(APIView):
    """GET /api/v1/geocode/?q= — address autocomplete suggestions."""

    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "")
        try:
            suggestions = factory.get_geocoder().suggest(query, limit=5)
        except ProviderUnavailable as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)


class TripHistoryView(APIView):
    """GET /api/v1/trips/ — paginated recent trips. DELETE — clear all."""

    def get(self, request: Request) -> Response:
        repo = factory.get_trip_repository()
        try:
            limit = min(max(int(request.query_params.get("limit", 5)), 1), 50)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            limit, offset = 5, 0
        return Response(
            {"trips": repo.list_recent(limit=limit, offset=offset), "total": repo.count()},
            status=status.HTTP_200_OK,
        )

    def delete(self, request: Request) -> Response:
        factory.get_trip_repository().clear()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TripDetailView(APIView):
    """GET /api/v1/trips/<id>/ — replay a stored trip. DELETE — remove it."""

    def get(self, request: Request, trip_id: int) -> Response:
        trip = factory.get_trip_repository().get(trip_id)
        if trip is None:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(trip, status=status.HTTP_200_OK)

    def delete(self, request: Request, trip_id: int) -> Response:
        ok = factory.get_trip_repository().delete(trip_id)
        if not ok:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HealthView(APIView):
    """GET /api/v1/health/ — liveness probe."""

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
