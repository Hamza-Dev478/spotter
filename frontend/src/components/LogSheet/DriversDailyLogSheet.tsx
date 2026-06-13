import type { DailyLog, LogMeta } from "../../types/trip";
import { fmtDateLong, fmtMiles, hoursToClock } from "../../lib/format";
import { LogGrid } from "./LogGrid";

interface Props {
  log: DailyLog;
  pageNumber: number;
  totalPages: number;
  meta?: LogMeta;
}

function LogField({ label, value, wide }: { label: string; value?: string; wide?: boolean }) {
  return (
    <div className="log-field" style={wide ? { gridColumn: "span 2" } : undefined}>
      <div className="lf-label">{label}</div>
      <div className="lf-value">{value || " "}</div>
    </div>
  );
}

export function DriversDailyLogSheet({ log, pageNumber, totalPages, meta = {} }: Props) {
  const remarks = log.segments.filter(
    (s) => s.locationLabel && s.locationLabel !== "Off duty",
  );

  const onDutyTotal = log.totals.driving + log.totals.onDuty;
  const offTotal = log.totals.offDuty + log.totals.sleeper;
  const tz = meta.homeTimezone?.trim();

  return (
    <div className="log-sheet" data-log-sheet={log.date}>
      <div className="log-sheet-title">
        <h3>Driver&apos;s Daily Log</h3>
        <span className="page-of">
          {fmtDateLong(log.date)} · Sheet {pageNumber} of {totalPages}
        </span>
      </div>

      <div className="log-cert">I certify that these entries are true and correct.</div>

      <div className="log-fields">
        <LogField label="Date" value={fmtDateLong(log.date)} />
        <LogField label="Total Miles Driving Today" value={fmtMiles(log.totalMilesDriving)} />
        <LogField label="Total Mileage Today" value={fmtMiles(log.totalMilesDriving)} />
        <LogField label="Name of Carrier" value={meta.carrierName} />
        <LogField label="Main Office Address" value={meta.mainOfficeAddress} wide />
        <LogField label="Vehicle / Trailer No." value={meta.vehicleNumbers} />
        <LogField label="Driver (signature)" value={meta.driverName} />
        <LogField label="Co-Driver" value={meta.coDriverName} />
      </div>

      <div className="log-timebase">
        Time base: {tz ? `${tz} (home terminal)` : "home-terminal time"}
      </div>

      <div className="log-grid-scroll">
        <LogGrid log={log} />
      </div>

      <div className="log-remarks">
        <h4>Remarks</h4>
        {remarks.length === 0 ? (
          <div className="remark-row">
            <span className="rk-time">—</span>
            <span>Off duty all day</span>
          </div>
        ) : (
          remarks.map((s, i) => (
            <div className="remark-row" key={i}>
              <span className="rk-time">{hoursToClock(s.startHour)}</span>
              <span>
                {s.locationLabel}
                {s.dutyStatus === "driving" && s.miles > 0 ? ` · ${fmtMiles(s.miles)}` : ""}
                {s.remark && s.remark !== s.locationLabel ? ` — ${s.remark}` : ""}
              </span>
            </div>
          ))
        )}
      </div>

      <div className="log-shipping">
        <h4>Shipping Documents</h4>
        <div className="ship-row">
          <span className="ship-k">Pro / Shipping No.</span>
          <span className="ship-v">{meta.shippingDocNumber || "—"}</span>
        </div>
        <div className="ship-row">
          <span className="ship-k">Shipper &amp; Commodity</span>
          <span className="ship-v">{meta.shipperCommodity || "—"}</span>
        </div>
      </div>

      <div className="log-recap">
        <h4>Recap · Hours of Service (70 hr / 8 day)</h4>
        <div className="recap-grid">
          <div className="recap-cell">
            <div className="rc-k">Driving (line 3)</div>
            <div className="rc-v">{log.totals.driving.toFixed(2)}</div>
          </div>
          <div className="recap-cell">
            <div className="rc-k">On-duty, not driving (line 4)</div>
            <div className="rc-v">{log.totals.onDuty.toFixed(2)}</div>
          </div>
          <div className="recap-cell">
            <div className="rc-k">Total on-duty (3 + 4)</div>
            <div className="rc-v">{onDutyTotal.toFixed(2)}</div>
          </div>
          <div className="recap-cell">
            <div className="rc-k">Off-duty + sleeper (1 + 2)</div>
            <div className="rc-v">{offTotal.toFixed(2)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
