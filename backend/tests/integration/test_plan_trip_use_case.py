"""Integration test: the PlanTrip use case wired to fake providers (no DB, no HTTP)."""

from __future__ import annotations

from datetime import datetime, timezone

from application.dtos.plan_trip_input import PlanTripInput
from application.use_cases.plan_trip import PlanTripUseCase
from domain.models.hos import HOSConstants
from domain.services.hos_scheduler import HOSScheduler
from tests.fakes import FakeGeocoder, FakeRouter


def _use_case(fuel_interval=1000.0):
    return PlanTripUseCase(
        geocoder=FakeGeocoder(),
        router=FakeRouter(),
        scheduler=HOSScheduler(HOSConstants(fuel_interval_miles=fuel_interval)),
        fuel_interval_miles=fuel_interval,
    )


def _input(current="Chicago", pickup="St Louis", dropoff="Dallas", cycle=0.0):
    return PlanTripInput(
        current_location=current,
        pickup_location=pickup,
        dropoff_location=dropoff,
        current_cycle_used_hours=cycle,
        start_time=datetime(2026, 6, 12, 6, 0, tzinfo=timezone.utc),
    )


def test_output_has_full_contract():
    result = _use_case().execute(_input())
    assert set(result) == {"summary", "route", "stops", "dailyLogs", "logMeta"}
    assert result["route"]["geometry"]["type"] == "LineString"
    assert len(result["route"]["legs"]) == 2
    assert result["summary"]["totalMiles"] > 0
    assert result["summary"]["days"] == len(result["dailyLogs"])


def test_stops_include_start_pickup_dropoff_in_mile_order():
    stops = _use_case().execute(_input())["stops"]
    types = [s["type"] for s in stops]
    assert types[0] == "start"
    assert types[-1] == "dropoff"
    assert "pickup" in types
    miles = [s["atMile"] for s in stops]
    assert miles == sorted(miles)


def test_long_trip_is_multi_day_and_each_day_sums_to_24h():
    # Chicago -> St Louis -> Dallas is ~800 mi / ~15h -> spans 2 days.
    result = _use_case().execute(_input())
    assert len(result["dailyLogs"]) >= 2
    for day in result["dailyLogs"]:
        assert abs(sum(day["totals"].values()) - 24.0) < 0.05


def test_fuel_stops_appear_for_long_routes():
    result = _use_case().execute(_input(current="Los Angeles", pickup="Denver", dropoff="Chicago"))
    assert result["summary"]["fuelStops"] >= 1
    assert any(s["type"] == "fuel" for s in result["stops"])


def test_remarks_are_enriched_with_city_state():
    # The fake reverse geocoder returns "...,  TS"; enriched labels carry it.
    result = _use_case().execute(_input())
    labels = [seg["locationLabel"] for day in result["dailyLogs"] for seg in day["segments"]]
    assert any(", TS" in label for label in labels)
    assert any("Pickup" in label for label in labels)
    assert any("Dropoff" in label for label in labels)


def test_log_meta_is_echoed_back():
    inp = PlanTripInput(
        current_location="Chicago",
        pickup_location="St Louis",
        dropoff_location="Dallas",
        current_cycle_used_hours=0.0,
        start_time=datetime(2026, 6, 12, 6, 0, tzinfo=timezone.utc),
        log_meta={"carrierName": "Acme Freight", "driverName": "Jane Doe"},
    )
    result = _use_case().execute(inp)
    assert result["logMeta"]["carrierName"] == "Acme Freight"
    assert result["logMeta"]["driverName"] == "Jane Doe"
