import type { TripSummary as Summary } from "../../types/trip";
import { fmtDateTime, fmtHours, fmtMiles } from "../../lib/format";

export function TripSummary({ summary }: { summary: Summary }) {
  const stats: { k: string; icon: string; v: React.ReactNode }[] = [
    { k: "Total distance", icon: "🛣️", v: fmtMiles(summary.totalMiles) },
    { k: "Driving time", icon: "🚚", v: fmtHours(summary.totalDriveHours) },
    {
      k: "Trip duration",
      icon: "⏱️",
      v: fmtHours(summary.totalDurationHours),
    },
    {
      k: "Log sheets",
      icon: "📋",
      v: (
        <>
          {summary.days} <small>day{summary.days === 1 ? "" : "s"}</small>
        </>
      ),
    },
    { k: "Fuel stops", icon: "⛽", v: summary.fuelStops },
    {
      k: "Cycle used (end)",
      icon: "🕒",
      v: (
        <>
          {summary.cycleHoursUsedAtEnd.toFixed(1)} <small>/ 70 hr</small>
        </>
      ),
    },
  ];

  return (
    <div>
      <div className="stat-grid">
        {stats.map((s) => (
          <div className="stat" key={s.k}>
            <div className="k">
              <span aria-hidden>{s.icon}</span>
              {s.k}
            </div>
            <div className="v">{s.v}</div>
          </div>
        ))}
      </div>
      <p style={{ color: "var(--muted)", fontSize: 13, margin: "10px 2px 0" }}>
        Estimated arrival <strong>{fmtDateTime(summary.estimatedCompletionTime)}</strong> · {summary.restStops}{" "}
        required rest period{summary.restStops === 1 ? "" : "s"}.
      </p>
    </div>
  );
}
