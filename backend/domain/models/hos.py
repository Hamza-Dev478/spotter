"""FMCSA Hours-of-Service domain model: duty statuses, rule constants, the
running clock state, and the timeline segment value object.

All values here come straight from 49 CFR 395.8 for property-carrying drivers.
Nothing in this module imports Django — it is pure, deterministic, and unit
testable without a database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class DutyStatus(str, Enum):
    """The four duty statuses drawn as rows on the FMCSA daily log."""

    OFF_DUTY = "off_duty"
    SLEEPER = "sleeper"
    DRIVING = "driving"
    ON_DUTY = "on_duty"  # on duty, not driving


@dataclass(frozen=True)
class HOSConstants:
    """Property-carrying, 70hr/8day rule set (single 10h off-duty reset model)."""

    drive_limit_hours: float = 11.0          # max driving after 10h off
    window_limit_hours: float = 14.0         # max on-duty window (elapsed)
    break_after_drive_hours: float = 8.0     # 30-min break required after 8h driving
    break_minutes: int = 30
    reset_off_duty_hours: float = 10.0       # consecutive off-duty to reset 11/14
    cycle_limit_hours: float = 70.0          # 70 on-duty hours / 8 days
    restart_hours: float = 34.0              # 34h off-duty restarts the cycle
    pickup_minutes: int = 60                 # 1h on-duty loading
    dropoff_minutes: int = 60                # 1h on-duty unloading
    fuel_minutes: int = 15                   # on-duty fueling stop
    fuel_interval_miles: float = 1000.0      # fuel at least every 1000 miles


@dataclass
class HOSState:
    """The driver's running clocks. Hours, not minutes, to match the rule book.

    Only `cycle_used_hours` is seeded from the request (`currentCycleUsedHrs`);
    the others assume the driver starts fresh after a 10h+ reset.
    """

    cycle_used_hours: float = 0.0       # toward the 70h cap (on-duty time only)
    drive_today_hours: float = 0.0      # toward the 11h driving cap
    window_used_hours: float = 0.0      # elapsed time toward the 14h window cap
    since_break_hours: float = 0.0      # driving since the last >=30min break

    def reset_after_off_duty(self) -> None:
        """A 10h+ off-duty period resets the daily driving/window/break clocks."""
        self.drive_today_hours = 0.0
        self.window_used_hours = 0.0
        self.since_break_hours = 0.0

    def restart_cycle(self) -> None:
        """A 34h+ off-duty period additionally restarts the 70h cycle."""
        self.reset_after_off_duty()
        self.cycle_used_hours = 0.0


@dataclass
class Segment:
    """One contiguous block of a single duty status on the timeline."""

    duty_status: DutyStatus
    start_time: datetime
    end_time: datetime
    miles: float = 0.0
    location_label: str = ""
    remark: str = ""

    @property
    def duration_minutes(self) -> int:
        return round((self.end_time - self.start_time).total_seconds() / 60)

    def to_dict(self) -> dict:
        return {
            "dutyStatus": self.duty_status.value,
            "startTime": self.start_time.isoformat().replace("+00:00", "Z"),
            "endTime": self.end_time.isoformat().replace("+00:00", "Z"),
            "durationMinutes": self.duration_minutes,
            "miles": round(self.miles, 1),
            "locationLabel": self.location_label,
            "remark": self.remark,
        }


def add_minutes(t: datetime, minutes: float) -> datetime:
    return t + timedelta(minutes=minutes)
