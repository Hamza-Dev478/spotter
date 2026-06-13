"""Input DTO for the plan-trip use case (framework-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PlanTripInput:
    current_location: str
    pickup_location: str
    dropoff_location: str
    current_cycle_used_hours: float
    start_time: datetime
    # Optional presentation-only metadata for the log sheets (driver, carrier,
    # shipping). The HOS engine ignores it; it is echoed back in the output.
    log_meta: dict = field(default_factory=dict)
