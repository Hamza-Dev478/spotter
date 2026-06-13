// Shapes mirror the Django API responses (api/v1/trips/plan/).

export type DutyStatus = "off_duty" | "sleeper" | "driving" | "on_duty";

export type StopType = "start" | "pickup" | "dropoff" | "fuel" | "rest";

export interface Segment {
  dutyStatus: DutyStatus;
  startTime: string;
  endTime: string;
  durationMinutes: number;
  miles: number;
  locationLabel: string;
  remark: string;
  startHour: number; // 0..24, day-relative — used directly by the SVG renderer
  endHour: number;
}

export interface DayTotals {
  offDuty: number;
  sleeper: number;
  driving: number;
  onDuty: number;
}

export interface DailyLog {
  date: string; // YYYY-MM-DD
  totalMilesDriving: number;
  totals: DayTotals;
  segments: Segment[];
}

export interface Stop {
  type: StopType;
  label: string;
  lat: number;
  lon: number;
  atMile: number;
}

export interface RouteLeg {
  from: string;
  to: string;
  distanceMiles: number;
  durationHours: number;
}

export interface TripRoute {
  geometry: { type: "LineString"; coordinates: [number, number][] }; // (lon, lat)
  legs: RouteLeg[];
}

export interface TripSummary {
  totalMiles: number;
  totalDriveHours: number;
  totalDurationHours: number;
  fuelStops: number;
  restStops: number;
  days: number;
  startTime: string;
  estimatedCompletionTime: string;
  cycleHoursUsedAtEnd: number;
}

// Optional, presentation-only details shown on the log sheets.
export interface LogMeta {
  carrierName?: string;
  mainOfficeAddress?: string;
  vehicleNumbers?: string;
  driverName?: string;
  coDriverName?: string;
  homeTimezone?: string;
  shippingDocNumber?: string;
  shipperCommodity?: string;
}

export interface TripPlan {
  summary: TripSummary;
  route: TripRoute;
  stops: Stop[];
  dailyLogs: DailyLog[];
  logMeta?: LogMeta;
}

export interface TripInput {
  currentLocation: string;
  pickupLocation: string;
  dropoffLocation: string;
  currentCycleUsedHrs: number;
  startTime?: string;
  logMeta?: LogMeta;
}

export interface Suggestion {
  label: string;
  lat: number;
  lon: number;
}

export interface TripHistoryItem {
  id: number;
  createdAt: string;
  currentLocation: string;
  pickupLocation: string;
  dropoffLocation: string;
  currentCycleUsedHrs: number;
  totalMiles: number;
  totalDriveHours: number;
  days: number;
}
