"""The HOS scheduling engine.

Given the planned route (legs with real OSRM drive time + distance) and the
driver's current cycle usage, produce an ordered, gap-free timeline of duty
segments that respects the FMCSA property-carrying rule set:

    * 11h driving limit          (after 10h off duty)
    * 14h on-duty window         (elapsed; not extended by breaks)
    * 30-min break after 8h cumulative driving
    * 10h consecutive off duty resets the 11h/14h clocks
    * 70h / 8-day cycle, restarted by 34h off duty
    * 1h on-duty pickup + 1h on-duty dropoff
    * 15-min on-duty fuel stop at least every 1000 miles

The algorithm is greedy and deterministic: each driving chunk is sized to the
tightest active constraint, so rest is only inserted when a rule forces it.

The trip is modelled in realistic order:
    drive current -> pickup  |  load 1h  |  drive pickup -> dropoff  |  unload 1h
"""

from __future__ import annotations

from datetime import datetime

from ..models.hos import DutyStatus, HOSConstants, HOSState, Segment, add_minutes
from ..models.trip import Route, RouteLeg


class HOSScheduler:
    def __init__(self, constants: HOSConstants | None = None) -> None:
        self.c = constants or HOSConstants()

    # -- public API ---------------------------------------------------------
    def build_schedule(
        self,
        route: Route,
        start_time: datetime,
        current_cycle_used_hours: float,
    ) -> list[Segment]:
        """Return the full, gap-free, merged duty timeline for the route."""
        state = HOSState(cycle_used_hours=max(0.0, current_cycle_used_hours))
        self._segments: list[Segment] = []
        self._t = start_time
        self._miles_done = 0.0
        self._next_fuel_at = self.c.fuel_interval_miles

        legs = [leg for leg in route.legs if leg.drive_hours > 0 and leg.distance_miles > 0]
        for index, leg in enumerate(legs):
            self._drive_leg(leg, state)
            is_pickup_leg = index == 0  # leg 0 ends at the pickup location
            if is_pickup_leg:
                self._on_duty(self.c.pickup_minutes, state, "Pickup", "Loading")

        self._on_duty(self.c.dropoff_minutes, state, "Dropoff", "Unloading")
        return _merge_adjacent(self._segments)

    # -- driving ------------------------------------------------------------
    def _drive_leg(self, leg: RouteLeg, state: HOSState) -> None:
        speed = leg.avg_speed_mph
        # Work on a whole-minute grid so the HOS clocks never drift or overshoot
        # their limits by sub-minute rounding error.
        leg_remaining_min = round(leg.drive_hours * 60.0)
        label = "Driving"

        while leg_remaining_min > 0:
            self._apply_mandatory_rest(state)

            # Minutes available before the next forced stop (all integer-valued).
            to_drive_limit = round((self.c.drive_limit_hours - state.drive_today_hours) * 60.0)
            to_window_limit = round((self.c.window_limit_hours - state.window_used_hours) * 60.0)
            to_break_limit = round((self.c.break_after_drive_hours - state.since_break_hours) * 60.0)
            to_cycle_limit = round((self.c.cycle_limit_hours - state.cycle_used_hours) * 60.0)
            to_fuel_min = round(((self._next_fuel_at - self._miles_done) / speed) * 60.0)

            chunk = min(
                leg_remaining_min,
                to_drive_limit,
                to_window_limit,
                to_break_limit,
                to_cycle_limit,  # stop driving exactly when the 70h cycle is exhausted
                to_fuel_min,
            )
            chunk = max(1, chunk)  # always make progress (guards fuel-boundary alignment)

            miles = speed * (chunk / 60.0)
            end = add_minutes(self._t, chunk)
            self._segments.append(
                Segment(
                    duty_status=DutyStatus.DRIVING,
                    start_time=self._t,
                    end_time=end,
                    miles=miles,
                    location_label=label,
                )
            )
            self._t = end
            state.drive_today_hours += chunk / 60.0
            state.window_used_hours += chunk / 60.0
            state.since_break_hours += chunk / 60.0
            state.cycle_used_hours += chunk / 60.0
            self._miles_done += miles
            leg_remaining_min -= chunk

            # Fuel boundary reached mid-trip -> on-duty fuel stop.
            if self._miles_done >= self._next_fuel_at - 0.5 and leg_remaining_min > 0:
                self._on_duty(
                    self.c.fuel_minutes,
                    state,
                    f"Fuel stop (~{int(self._next_fuel_at)} mi)",
                    "Fueling",
                )
                self._next_fuel_at += self.c.fuel_interval_miles

    # -- non-driving inserts -----------------------------------------------
    def _apply_mandatory_rest(self, state: HOSState) -> None:
        """Insert the rest a rule forces *before* the next driving chunk."""
        # 70h cycle exhausted -> 34h restart (also clears daily clocks).
        if state.cycle_used_hours >= self.c.cycle_limit_hours:
            self._off_duty(self.c.restart_hours * 60.0, state, "34-hour restart", restart=True)

        # 11h driving or 14h window hit -> 10h off duty.
        if (
            state.drive_today_hours >= self.c.drive_limit_hours - 1e-6
            or state.window_used_hours >= self.c.window_limit_hours - 1e-6
        ):
            self._off_duty(self.c.reset_off_duty_hours * 60.0, state, "10-hour reset", reset=True)

        # 8h cumulative driving without a break -> 30-min break (only if there is
        # still room to drive afterward, otherwise the reset above handles it).
        if state.since_break_hours >= self.c.break_after_drive_hours - 1e-6:
            self._off_duty(self.c.break_minutes, state, "30-minute break")

    def _on_duty(self, minutes: int, state: HOSState, label: str, remark: str) -> None:
        end = add_minutes(self._t, minutes)
        self._segments.append(
            Segment(
                duty_status=DutyStatus.ON_DUTY,
                start_time=self._t,
                end_time=end,
                location_label=label,
                remark=remark,
            )
        )
        self._t = end
        hours = minutes / 60.0
        state.window_used_hours += hours
        state.cycle_used_hours += hours
        # >=30min of non-driving satisfies the 8h driving-break requirement.
        if minutes >= self.c.break_minutes:
            state.since_break_hours = 0.0

    def _off_duty(
        self,
        minutes: float,
        state: HOSState,
        label: str,
        *,
        reset: bool = False,
        restart: bool = False,
    ) -> None:
        end = add_minutes(self._t, minutes)
        self._segments.append(
            Segment(
                duty_status=DutyStatus.OFF_DUTY,
                start_time=self._t,
                end_time=end,
                location_label=label,
                remark=label,
            )
        )
        self._t = end
        if restart:
            state.restart_cycle()
        elif reset:
            state.reset_after_off_duty()
        else:
            state.since_break_hours = 0.0
            state.window_used_hours += minutes / 60.0


def _merge_adjacent(segments: list[Segment]) -> list[Segment]:
    """Collapse consecutive segments that share a duty status (keeps logs clean)."""
    merged: list[Segment] = []
    for seg in segments:
        if merged and merged[-1].duty_status == seg.duty_status:
            prev = merged[-1]
            prev.end_time = seg.end_time
            prev.miles += seg.miles
            if seg.location_label and seg.location_label not in prev.location_label:
                prev.location_label = f"{prev.location_label} + {seg.location_label}".strip(" +")
        else:
            merged.append(seg)
    return merged
