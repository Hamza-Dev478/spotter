import type { Segment } from "../types/trip";
import { DUTY_META } from "./dutyStatus";

// Layout of one FMCSA daily-log grid, in SVG user units. A fixed viewBox lets
// the same coordinates serve both the on-screen render and PNG/PDF export.
export const LOG_GRID = {
  labelWidth: 132, // left "Off Duty / Sleeper / ..." labels
  hourWidth: 30, // width of one hour column
  rowHeight: 34, // height of one duty row
  totalsWidth: 60, // right "Total Hours" column
  topPad: 28, // space above the grid for the hour numbers
  bottomPad: 14,
} as const;

export const GRID_WIDTH = LOG_GRID.hourWidth * 24;
export const GRID_LEFT = LOG_GRID.labelWidth;
export const GRID_RIGHT = GRID_LEFT + GRID_WIDTH;
export const SVG_WIDTH = LOG_GRID.labelWidth + GRID_WIDTH + LOG_GRID.totalsWidth;
export const GRID_TOP = LOG_GRID.topPad;
export const GRID_BOTTOM = GRID_TOP + LOG_GRID.rowHeight * 4;
export const SVG_HEIGHT = GRID_BOTTOM + LOG_GRID.bottomPad;

/** X pixel for a fractional hour 0..24. */
export const xForHour = (hour: number): number =>
  GRID_LEFT + Math.max(0, Math.min(24, hour)) * LOG_GRID.hourWidth;

export const rowTopY = (row: number): number => GRID_TOP + row * LOG_GRID.rowHeight;
export const rowCenterY = (row: number): number => rowTopY(row) + LOG_GRID.rowHeight / 2;

/**
 * Build the continuous step-line `d` attribute: a horizontal run along each
 * segment's duty row, with a vertical connector wherever the status changes.
 */
export function buildDutyPath(segments: Segment[]): string {
  if (segments.length === 0) return "";
  const parts: string[] = [];
  let prevRow: number | null = null;

  for (const seg of segments) {
    const row = DUTY_META[seg.dutyStatus].row;
    const y = rowCenterY(row);
    const x1 = xForHour(seg.startHour);
    const x2 = xForHour(seg.endHour);

    if (prevRow === null) {
      parts.push(`M ${x1.toFixed(2)} ${y.toFixed(2)}`);
    } else if (prevRow !== row) {
      // vertical connector at the shared boundary x
      parts.push(`L ${x1.toFixed(2)} ${y.toFixed(2)}`);
    }
    parts.push(`L ${x2.toFixed(2)} ${y.toFixed(2)}`);
    prevRow = row;
  }
  return parts.join(" ");
}
