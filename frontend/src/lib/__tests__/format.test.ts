import { describe, it, expect } from "vitest";
import { hoursToClock, fmtMiles, fmtHours, shortenLocation } from "../format";

describe("format", () => {
  it("hoursToClock renders day-relative HH:MM", () => {
    expect(hoursToClock(9.5)).toBe("09:30");
    expect(hoursToClock(0)).toBe("00:00");
    expect(hoursToClock(13.25)).toBe("13:15");
  });

  it("fmtMiles rounds to whole miles", () => {
    expect(fmtMiles(925)).toBe("925 mi");
    expect(fmtMiles(0)).toBe("0 mi");
  });

  it("fmtHours formats whole and partial hours", () => {
    expect(fmtHours(2)).toBe("2 hr");
    expect(fmtHours(2.5)).toBe("2h 30m");
  });

  it("shortenLocation abbreviates US states and keeps short names", () => {
    expect(shortenLocation("Denver, Colorado, United States")).toBe("Denver, CO");
    expect(shortenLocation("St. Louis, MO")).toBe("St. Louis, MO");
    expect(
      shortenLocation("Chicago, South Chicago Township, Cook County, Illinois, United States"),
    ).toBe("Chicago, IL");
  });
});
