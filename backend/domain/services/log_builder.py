"""Turn a flat duty timeline into per-day log sheets.

The scheduler produces a gap-free list of segments from the trip's start to its
end. To render FMCSA daily logs we must:

    1. pad off-duty time before the first segment (back to that day's midnight)
       and after the last segment (forward to the final midnight), so the whole
       timeline is continuous from 00:00 of day 1 to 24:00 of the last day;
    2. split any segment that crosses midnight into per-day pieces;
    3. group by calendar date and total each duty status.

Because the timeline is continuous and gap-free, every resulting day sums to
exactly 24.0 hours.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..models.hos import DutyStatus, Segment

_ALL_STATUSES = [
    DutyStatus.OFF_DUTY,
    DutyStatus.SLEEPER,
    DutyStatus.DRIVING,
    DutyStatus.ON_DUTY,
]


def _midnight(t: datetime) -> datetime:
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


def build_daily_logs(segments: list[Segment]) -> list[dict]:
    if not segments:
        return []

    timeline = _pad_to_full_days(segments)
    pieces_by_date: dict[str, list[tuple[Segment, float, float]]] = {}

    for seg in timeline:
        for piece, day, start_h, end_h in _split_at_midnight(seg):
            pieces_by_date.setdefault(day, []).append((piece, start_h, end_h))

    logs: list[dict] = []
    for day in sorted(pieces_by_date):
        pieces = pieces_by_date[day]
        totals = {s.value: 0.0 for s in _ALL_STATUSES}
        miles = 0.0
        out_segments = []
        for piece, start_h, end_h in pieces:
            totals[piece.duty_status.value] += end_h - start_h
            miles += piece.miles
            out_segments.append(
                {
                    **piece.to_dict(),
                    "startHour": round(start_h, 4),
                    "endHour": round(end_h, 4),
                }
            )
        logs.append(
            {
                "date": day,
                "totalMilesDriving": round(miles, 1),
                "totals": {
                    "offDuty": round(totals[DutyStatus.OFF_DUTY.value], 2),
                    "sleeper": round(totals[DutyStatus.SLEEPER.value], 2),
                    "driving": round(totals[DutyStatus.DRIVING.value], 2),
                    "onDuty": round(totals[DutyStatus.ON_DUTY.value], 2),
                },
                "segments": out_segments,
            }
        )
    return logs


def _pad_to_full_days(segments: list[Segment]) -> list[Segment]:
    start = segments[0].start_time
    end = segments[-1].end_time
    padded = list(segments)

    day_start = _midnight(start)
    if start > day_start:
        padded.insert(
            0,
            Segment(DutyStatus.OFF_DUTY, day_start, start, location_label="Off duty"),
        )

    final_midnight = _midnight(end)
    if end > final_midnight:  # trip ends mid-day -> pad to the next midnight
        final_midnight = final_midnight + timedelta(days=1)
    if end < final_midnight:
        padded.append(
            Segment(DutyStatus.OFF_DUTY, end, final_midnight, location_label="Off duty"),
        )
    return padded


def _split_at_midnight(seg: Segment):
    """Yield (piece, 'YYYY-MM-DD', start_hour, end_hour) for each day touched."""
    cursor = seg.start_time
    while cursor < seg.end_time:
        day_midnight = _midnight(cursor)
        next_midnight = day_midnight + timedelta(days=1)
        piece_end = min(seg.end_time, next_midnight)

        start_h = (cursor - day_midnight).total_seconds() / 3600.0
        end_h = (piece_end - day_midnight).total_seconds() / 3600.0

        # Apportion miles by time share so per-day mileage stays consistent.
        full = (seg.end_time - seg.start_time).total_seconds()
        share = ((piece_end - cursor).total_seconds() / full) if full else 1.0
        piece = Segment(
            duty_status=seg.duty_status,
            start_time=cursor,
            end_time=piece_end,
            miles=seg.miles * share,
            location_label=seg.location_label,
            remark=seg.remark,
        )
        yield piece, day_midnight.date().isoformat(), start_h, end_h
        cursor = piece_end
