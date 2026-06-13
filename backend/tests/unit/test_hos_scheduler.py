"""Unit tests for the pure HOS scheduling engine (no Django, no DB)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.models.hos import DutyStatus, HOSConstants
from domain.models.location import LatLng
from domain.models.trip import Route, RouteLeg
from domain.services.hos_scheduler import HOSScheduler
from domain.services.log_builder import build_daily_logs

START = datetime(2026, 6, 12, 6, 0, tzinfo=timezone.utc)
A = LatLng(41.88, -87.63)
B = LatLng(38.62, -90.19)


def leg(distance_miles: float, drive_hours: float) -> RouteLeg:
    return RouteLeg(
        origin=A,
        destination=B,
        distance_miles=distance_miles,
        drive_hours=drive_hours,
        geometry=[A.as_lon_lat(), B.as_lon_lat()],
    )


def route(*legs: RouteLeg) -> Route:
    return Route(legs=list(legs), geometry=[A.as_lon_lat(), B.as_lon_lat()])


def schedule(r: Route, cycle_used: float = 0.0):
    return HOSScheduler().build_schedule(r, START, cycle_used)


def hours(segments, status: DutyStatus) -> float:
    return sum(s.duration_minutes for s in segments if s.duty_status == status) / 60.0


# --- contiguity & totals ----------------------------------------------------
def test_timeline_is_gap_free():
    segs = schedule(route(leg(100, 2), leg(100, 2)))
    for prev, nxt in zip(segs, segs[1:]):
        assert prev.end_time == nxt.start_time


def test_short_trip_has_pickup_dropoff_and_no_rest():
    # 4h driving, under every limit -> just drive/pickup/drive/dropoff.
    segs = schedule(route(leg(110, 2), leg(110, 2)))
    assert hours(segs, DutyStatus.DRIVING) == pytest.approx(4.0, abs=0.05)
    assert hours(segs, DutyStatus.ON_DUTY) == pytest.approx(2.0, abs=0.05)  # 1h+1h
    # No 10h reset inserted on a short trip.
    assert all(s.duration_minutes < 10 * 60 for s in segs)
    labels = " ".join(s.location_label for s in segs)
    assert "Pickup" in labels and "Dropoff" in labels


# --- daily logs always cover 24h -------------------------------------------
@pytest.mark.parametrize(
    "r,cycle",
    [
        (route(leg(110, 2), leg(110, 2)), 0.0),
        (route(leg(600, 10), leg(900, 15)), 0.0),  # multi-day
        (route(leg(60, 1), leg(60, 1)), 69.5),  # forces 34h restart
    ],
)
def test_every_daily_log_sums_to_24h(r, cycle):
    logs = build_daily_logs(schedule(r, cycle))
    assert logs
    for day in logs:
        total = sum(day["totals"].values())
        assert total == pytest.approx(24.0, abs=0.05), day["date"]


# --- 11h / 14h limits over a long trip --------------------------------------
def test_long_trip_respects_driving_limit_and_spans_multiple_days():
    # 1500 miles @ 60 mph = 25h driving -> needs 10h resets, multiple days.
    segs = schedule(route(leg(750, 12.5), leg(750, 12.5)))
    logs = build_daily_logs(segs)
    assert len(logs) >= 2

    # No single duty period drives more than 11h before a 10h+ reset appears.
    drive_since_reset = 0.0
    for s in segs:
        if s.duty_status == DutyStatus.DRIVING:
            drive_since_reset += s.duration_minutes / 60.0
            assert drive_since_reset <= 11.0 + 1e-6
        elif s.duty_status == DutyStatus.OFF_DUTY and s.duration_minutes >= 10 * 60:
            drive_since_reset = 0.0


def test_window_never_allows_driving_past_14h():
    segs = schedule(route(leg(750, 12.5), leg(750, 12.5)))
    window_used = 0.0
    for s in segs:
        if s.duty_status == DutyStatus.OFF_DUTY and s.duration_minutes >= 10 * 60:
            window_used = 0.0
        else:
            if s.duty_status == DutyStatus.DRIVING:
                # Driving must start within the 14h window.
                assert window_used <= 14.0 + 1e-6
            window_used += s.duration_minutes / 60.0


# --- fuel stops -------------------------------------------------------------
def test_fuel_stop_inserted_every_1000_miles():
    segs = schedule(route(leg(600, 10), leg(700, 11)))  # 1300 miles -> 1 fuel stop
    fuel = [s for s in segs if "Fuel" in s.location_label]
    assert len(fuel) >= 1
    assert all(s.duty_status == DutyStatus.ON_DUTY for s in fuel)


def test_fuel_interval_is_configurable():
    sched = HOSScheduler(HOSConstants(fuel_interval_miles=500))
    segs = sched.build_schedule(route(leg(600, 10), leg(0.0, 0.0)), START, 0.0)
    fuel = [s for s in segs if "Fuel" in s.location_label]
    assert len(fuel) >= 1


def test_fuel_pickup_dropoff_segments_are_on_duty():
    # §395.2: fueling and loading/unloading are on-duty (not driving).
    segs = schedule(route(leg(600, 10), leg(700, 11)))  # 1300 mi -> a fuel stop
    pickups = [s for s in segs if s.location_label == "Pickup"]
    dropoffs = [s for s in segs if s.location_label == "Dropoff"]
    fuels = [s for s in segs if s.location_label.startswith("Fuel")]
    assert pickups and all(s.duty_status == DutyStatus.ON_DUTY for s in pickups)
    assert dropoffs and all(s.duty_status == DutyStatus.ON_DUTY for s in dropoffs)
    assert fuels and all(s.duty_status == DutyStatus.ON_DUTY for s in fuels)


# --- 30-minute break --------------------------------------------------------
def test_thirty_minute_break_after_8h_continuous_driving():
    # A single 10h driving leg (no intervening on-duty) must trigger a 30-min break.
    segs = HOSScheduler().build_schedule(route(leg(550, 10), leg(0.0, 0.0)), START, 0.0)
    breaks = [
        s for s in segs if s.duty_status == DutyStatus.OFF_DUTY and s.duration_minutes == 30
    ]
    assert len(breaks) >= 1
    # The break lands at the 8-hour driving mark, never later.
    drive_before_break = 0.0
    for s in segs:
        if s.duty_status == DutyStatus.DRIVING:
            drive_before_break += s.duration_minutes / 60.0
        elif s.duty_status == DutyStatus.OFF_DUTY and s.duration_minutes == 30:
            assert drive_before_break <= 8.0 + 1e-6
            break


# --- 34h restart ------------------------------------------------------------
def test_cycle_exhaustion_triggers_34h_restart():
    segs = schedule(route(leg(60, 1), leg(60, 1)), cycle_used=69.5)
    restarts = [s for s in segs if s.duty_status == DutyStatus.OFF_DUTY and s.duration_minutes == 34 * 60]
    assert len(restarts) == 1


def test_70h_cycle_is_never_exceeded_while_on_duty():
    # Begin near the cap on a long trip: the engine must restart before the
    # cumulative on-duty time ever passes 70 hours.
    segs = schedule(route(leg(750, 12.5), leg(750, 12.5)), cycle_used=66.0)
    cycle = 66.0
    for s in segs:
        if s.duty_status in (DutyStatus.DRIVING, DutyStatus.ON_DUTY):
            cycle += s.duration_minutes / 60.0
            assert cycle <= 70.0 + 1e-6
        elif s.duty_status == DutyStatus.OFF_DUTY and s.duration_minutes >= 34 * 60:
            cycle = 0.0
