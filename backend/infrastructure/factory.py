"""Composition root: pick concrete provider/repository implementations.

This is the only place that knows which infrastructure classes are wired in, so
swapping OSRM for OpenRouteService (or the ORM repo for a fake) is a one-line
change here and nowhere else.
"""

from __future__ import annotations

from application.interfaces.geocoding import IGeocodingService
from application.interfaces.routing import IRoutingService
from application.interfaces.trip_repository import ITripRepository

from .geocoding.nominatim_geocoder import NominatimGeocoder
from .persistence.trip_repository import DjangoTripRepository
from .routing.osrm_router import OSRMRouter


def get_geocoder() -> IGeocodingService:
    return NominatimGeocoder()


def get_router() -> IRoutingService:
    return OSRMRouter()


def get_trip_repository() -> ITripRepository:
    return DjangoTripRepository()
