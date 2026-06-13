import { describe, it, expect } from "vitest";
import { buildDutyPath, xForHour, rowCenterY, GRID_LEFT, GRID_RIGHT } from "../logGeometry";
import type { DutyStatus, Segment } from "../../types/trip";

const seg = (dutyStatus: DutyStatus, startHour: number, endHour: number): Segment => ({
  dutyStatus,
  startHour,
  endHour,
  startTime: "",
  endTime: "",
  durationMinutes: Math.round((endHour - startHour) * 60),
  miles: 0,
  locationLabel: "",
  remark: "",
});

describe("logGeometry", () => {
  it("xForHour spans the grid and is monotonic", () => {
    expect(xForHour(0)).toBe(GRID_LEFT);
    expect(xForHour(24)).toBe(GRID_RIGHT);
    expect(xForHour(12)).toBeGreaterThan(xForHour(6));
  });

  it("xForHour clamps out-of-range hours", () => {
    expect(xForHour(-5)).toBe(GRID_LEFT);
    expect(xForHour(30)).toBe(GRID_RIGHT);
  });

  it("buildDutyPath returns empty string for no segments", () => {
    expect(buildDutyPath([])).toBe("");
  });

  it("buildDutyPath draws a step line with a vertical transition on status change", () => {
    const d = buildDutyPath([seg("off_duty", 0, 6), seg("driving", 6, 11)]);
    expect(d.startsWith("M")).toBe(true);
    expect(d).toContain("L");
    // both the off-duty row and the driving row y-coordinates appear
    expect(d).toContain(rowCenterY(0).toFixed(2));
    expect(d).toContain(rowCenterY(2).toFixed(2));
  });
});
