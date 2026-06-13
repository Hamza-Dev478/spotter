import { Fragment } from "react";
import type { DailyLog } from "../../types/trip";
import { DUTY_META, DUTY_ROWS } from "../../lib/dutyStatus";
import {
  GRID_BOTTOM,
  GRID_LEFT,
  GRID_RIGHT,
  GRID_TOP,
  LOG_GRID,
  SVG_HEIGHT,
  SVG_WIDTH,
  buildDutyPath,
  rowCenterY,
  rowTopY,
  xForHour,
} from "../../lib/logGeometry";

const HOURS = Array.from({ length: 25 }, (_, h) => h); // 0..24 gridlines

function hourLabel(h: number): string {
  if (h === 0 || h === 24) return "MID";
  if (h === 12) return "NOON";
  return String(h % 12 === 0 ? 12 : h % 12);
}

const TOTAL_BY_ROW = (log: DailyLog) => [
  log.totals.offDuty,
  log.totals.sleeper,
  log.totals.driving,
  log.totals.onDuty,
];

export function LogGrid({ log }: { log: DailyLog }) {
  const dutyPath = buildDutyPath(log.segments);
  const rowTotals = TOTAL_BY_ROW(log);
  const grand = rowTotals.reduce((a, b) => a + b, 0);

  return (
    <svg
      className="log-svg"
      viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
      role="img"
      aria-label={`Duty status grid for ${log.date}`}
    >
      {/* alternating row backgrounds */}
      {DUTY_ROWS.map((status, r) => (
        <rect
          key={`bg-${status}`}
          x={GRID_LEFT}
          y={rowTopY(r)}
          width={GRID_RIGHT - GRID_LEFT}
          height={LOG_GRID.rowHeight}
          fill={r % 2 === 0 ? "#ffffff" : "#fbfcfe"}
        />
      ))}

      {/* hour gridlines + labels */}
      {HOURS.map((h) => {
        const x = xForHour(h);
        const major = h % 6 === 0;
        return (
          <Fragment key={`h-${h}`}>
            <line
              x1={x}
              y1={GRID_TOP}
              x2={x}
              y2={GRID_BOTTOM}
              stroke={major ? "#64748b" : "#aab4c4"}
              strokeWidth={major ? 1.1 : 0.7}
            />
            <text
              x={x}
              y={GRID_TOP - 9}
              textAnchor="middle"
              fontSize={h === 0 || h === 12 || h === 24 ? 8 : 8.5}
              fontWeight={600}
              fill="#475569"
            >
              {hourLabel(h)}
            </text>
          </Fragment>
        );
      })}

      {/* quarter-hour ticks at the top & bottom edge of each row */}
      {DUTY_ROWS.map((_, r) =>
        HOURS.slice(0, 24).map((h) =>
          [1, 2, 3].map((q) => {
            const x = xForHour(h + q / 4);
            const len = q === 2 ? 9 : 5.5;
            const yTop = rowTopY(r);
            const yBot = rowTopY(r + 1);
            return (
              <Fragment key={`t-${r}-${h}-${q}`}>
                <line x1={x} y1={yTop} x2={x} y2={yTop + len} stroke="#c3ccd9" strokeWidth={0.6} />
                <line x1={x} y1={yBot - len} x2={x} y2={yBot} stroke="#c3ccd9" strokeWidth={0.6} />
              </Fragment>
            );
          }),
        ),
      )}

      {/* row separators + left labels + per-row total */}
      {DUTY_ROWS.map((status, r) => (
        <Fragment key={`row-${status}`}>
          <line
            x1={GRID_LEFT}
            y1={rowTopY(r)}
            x2={GRID_RIGHT}
            y2={rowTopY(r)}
            stroke="#334155"
            strokeWidth={0.9}
          />
          <text x={10} y={rowCenterY(r) - 4} fontSize={10.5} fontWeight={700} fill="#0f172a">
            {r + 1}.
          </text>
          <text x={24} y={rowCenterY(r) - 4} fontSize={10.5} fontWeight={600} fill="#1e293b">
            {DUTY_META[status].label.replace(" (not driving)", "")}
          </text>
          {DUTY_META[status].label.includes("not driving") && (
            <text x={24} y={rowCenterY(r) + 8} fontSize={8} fill="#64748b">
              (not driving)
            </text>
          )}
          <text
            x={GRID_RIGHT + LOG_GRID.totalsWidth / 2}
            y={rowCenterY(r) + 4}
            textAnchor="middle"
            fontSize={12}
            fontWeight={700}
            fill="#0f172a"
          >
            {rowTotals[r].toFixed(2)}
          </text>
        </Fragment>
      ))}

      {/* grid outer border */}
      <rect
        x={GRID_LEFT}
        y={GRID_TOP}
        width={GRID_RIGHT - GRID_LEFT}
        height={GRID_BOTTOM - GRID_TOP}
        fill="none"
        stroke="#334155"
        strokeWidth={1.2}
      />

      {/* totals column header + grand total */}
      <text
        x={GRID_RIGHT + LOG_GRID.totalsWidth / 2}
        y={GRID_TOP - 9}
        textAnchor="middle"
        fontSize={8}
        fontWeight={700}
        fill="#475569"
      >
        TOTAL
      </text>
      <line
        x1={GRID_RIGHT}
        y1={GRID_TOP}
        x2={GRID_RIGHT}
        y2={GRID_BOTTOM + 16}
        stroke="#334155"
        strokeWidth={1.2}
      />
      <text
        x={GRID_RIGHT + LOG_GRID.totalsWidth / 2}
        y={GRID_BOTTOM + 12}
        textAnchor="middle"
        fontSize={11}
        fontWeight={700}
        fill="#3730a3"
      >
        {grand.toFixed(2)}
      </text>

      {/* the duty-status step line */}
      <path
        d={dutyPath}
        fill="none"
        stroke="#111827"
        strokeWidth={2.4}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
