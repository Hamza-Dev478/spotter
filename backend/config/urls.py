"""Root URL configuration for the ELD Trip Planner API."""

from django.contrib import admin
from django.urls import path

from interface_adapters.views.trip_view import (
    GeocodeSuggestView,
    HealthView,
    TripDetailView,
    TripHistoryView,
    TripPlannerView,
)

api = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"{api}health/", HealthView.as_view(), name="health"),
    path(f"{api}trips/plan/", TripPlannerView.as_view(), name="plan-trip"),
    path(f"{api}geocode/", GeocodeSuggestView.as_view(), name="geocode-suggest"),
    path(f"{api}trips/", TripHistoryView.as_view(), name="trip-history"),
    path(f"{api}trips/<int:trip_id>/", TripDetailView.as_view(), name="trip-detail"),
]
