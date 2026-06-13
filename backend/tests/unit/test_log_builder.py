"""Unit tests for the per-day log builder (midnight splitting, 24h coverage)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.models.hos import DutyStatus, Segment
from domain.services.log_builder import build_daily_logs


def seg(status, start, end, miles=0.0):
    return Segment(status, start, end, miles=miles)


def test_empty_timeline_returns_no_logs():
    assert build_daily_logs([]) == []


def test_single_day_pads_off_duty_to_full_24h():
    start = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)
    logs = build_daily_logs([seg(DutyStatus.DRIVING, start, end, miles=200)])
    assert len(logs) == 1
    day = logs[0]
    assert day["date"] == "2026-06-12"
    assert day["totals"]["driving"] == pytest.approx(4.0, abs=0.01)
    assert day["totals"]["offDuty"] == pytest.approx(20.0, abs=0.01)
    assert sum(day["totals"].values()) == pytest.approx(24.0, abs=0.01)
    assert day["totalMilesDriving"] == pytest.approx(200.0, abs=0.1)


def test_segment_crossing_midnight_splits_into_two_days():
    start = datetime(2026, 6, 12, 22, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 13, 6, 0, tzinfo=timezone.utc)  # 8h overnight off-duty
    logs = build_daily_logs([seg(DutyStatus.SLEEPER, start, end)])
    assert [d["date"] for d in logs] == ["2026-06-12", "2026-06-13"]
    for day in logs:
        assert sum(day["totals"].values()) == pytest.approx(24.0, abs=0.01)
    # Day 1 sleeper = 22:00->24:00 = 2h; day 2 sleeper = 00:00->06:00 = 6h.
    assert logs[0]["totals"]["sleeper"] == pytest.approx(2.0, abs=0.01)
    assert logs[1]["totals"]["sleeper"] == pytest.approx(6.0, abs=0.01)


def test_segment_hours_are_day_relative_for_rendering():
    start = datetime(2026, 6, 12, 9, 30, tzinfo=timezone.utc)
    end = datetime(2026, 6, 12, 11, 0, tzinfo=timezone.utc)
    logs = build_daily_logs([seg(DutyStatus.DRIVING, start, end)])
    driving = [s for s in logs[0]["segments"] if s["dutyStatus"] == "driving"][0]
    assert driving["startHour"] == pytest.approx(9.5, abs=0.001)
    assert driving["endHour"] == pytest.approx(11.0, abs=0.001)


def test_miles_apportioned_across_midnight_by_time_share():
    start = datetime(2026, 6, 12, 20, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 13, 4, 0, tzinfo=timezone.utc)  # 8h, 4h each side
    logs = build_daily_logs([seg(DutyStatus.DRIVING, start, end, miles=400)])
    assert logs[0]["totalMilesDriving"] == pytest.approx(200.0, abs=0.5)
    assert logs[1]["totalMilesDriving"] == pytest.approx(200.0, abs=0.5)
