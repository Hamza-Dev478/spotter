import type { DutyStatus, StopType } from "../types/trip";

// Row order matches the FMCSA paper log top-to-bottom.
export const DUTY_META: Record<
  DutyStatus,
  { label: string; short: string; color: string; row: number }
> = {
  off_duty: { label: "Off Duty", short: "1", color: "#94a3b8", row: 0 },
  sleeper: { label: "Sleeper Berth", short: "2", color: "#8b5cf6", row: 1 },
  driving: { label: "Driving", short: "3", color: "#2563eb", row: 2 },
  on_duty: { label: "On Duty (not driving)", short: "4", color: "#f59e0b", row: 3 },
};

export const DUTY_ROWS: DutyStatus[] = ["off_duty", "sleeper", "driving", "on_duty"];

export const STOP_META: Record<StopType, { label: string; color: string; glyph: string }> = {
  start: { label: "Start", color: "#2563eb", glyph: "●" },
  pickup: { label: "Pickup", color: "#16a34a", glyph: "▲" },
  dropoff: { label: "Dropoff", color: "#dc2626", glyph: "■" },
  fuel: { label: "Fuel", color: "#f59e0b", glyph: "⛽" },
  rest: { label: "Rest", color: "#8b5cf6", glyph: "🛌" },
};
