import { useState } from "react";
import { LocationInput } from "./LocationInput";
import { ClockIcon, GaugeIcon, PlusIcon, RouteIcon, SparkleIcon, TruckIcon } from "../icons";
import type { LogMeta, TripInput } from "../../types/trip";

interface Props {
  onSubmit: (input: TripInput) => void;
  isSubmitting: boolean;
  prefill?: Partial<TripInput>;
  onResetResult?: () => void;
}

// Module-level so its identity is stable across renders (avoids input remount/focus loss).
function MetaField({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: string;
  placeholder?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="field" style={{ marginBottom: 10 }}>
      <label>{label}</label>
      <input
        className="input"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

interface Errors {
  currentLocation?: string;
  pickupLocation?: string;
  dropoffLocation?: string;
}

const SAMPLE = {
  currentLocation: "Chicago, IL",
  pickupLocation: "St. Louis, MO",
  dropoffLocation: "Dallas, TX",
  cycle: 14,
};

function defaultStart(): string {
  const d = new Date();
  d.setMinutes(0, 0, 0); // round to the hour for a tidy default
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Stored start times are the home-terminal wall-clock with a trailing Z, so a
// plain slice round-trips them back into the datetime-local input.
function isoToLocalInput(iso?: string): string {
  return iso ? iso.slice(0, 16) : defaultStart();
}

export function TripForm({ onSubmit, isSubmitting, prefill, onResetResult }: Props) {
  const [currentLocation, setCurrent] = useState(prefill?.currentLocation ?? "");
  const [pickupLocation, setPickup] = useState(prefill?.pickupLocation ?? "");
  const [dropoffLocation, setDropoff] = useState(prefill?.dropoffLocation ?? "");
  const [cycle, setCycle] = useState(prefill?.currentCycleUsedHrs ?? 0);
  const [startTime, setStartTime] = useState(() => isoToLocalInput(prefill?.startTime));
  const [meta, setMeta] = useState<LogMeta>(prefill?.logMeta ?? {});
  const [errors, setErrors] = useState<Errors>({});

  const setMetaField = (k: keyof LogMeta) => (v: string) => setMeta((m) => ({ ...m, [k]: v }));

  const validate = (): boolean => {
    const next: Errors = {};
    if (!currentLocation.trim()) next.currentLocation = "Required";
    if (!pickupLocation.trim()) next.pickupLocation = "Required";
    if (!dropoffLocation.trim()) next.dropoffLocation = "Required";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      currentLocation: currentLocation.trim(),
      pickupLocation: pickupLocation.trim(),
      dropoffLocation: dropoffLocation.trim(),
      currentCycleUsedHrs: cycle,
      startTime: startTime ? `${startTime}:00Z` : undefined,
      logMeta: meta,
    });
  };

  const fillSample = () => {
    setCurrent(SAMPLE.currentLocation);
    setPickup(SAMPLE.pickupLocation);
    setDropoff(SAMPLE.dropoffLocation);
    setCycle(SAMPLE.cycle);
    // Start the sample at 06:00 today so the demo logs read cleanly.
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    setStartTime(`${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T06:00`);
    setMeta({
      carrierName: "Acme Freight LLC",
      mainOfficeAddress: "Chicago, IL",
      vehicleNumbers: "TRK-4021 / TRL-88",
      driverName: "Jane Doe",
      homeTimezone: "CST",
      shippingDocNumber: "BOL-100423",
      shipperCommodity: "Palletized consumer goods",
    });
    setErrors({});
    onResetResult?.(); // clear any shown result -> back to the empty state until re-planned
  };

  const resetForm = () => {
    setCurrent("");
    setPickup("");
    setDropoff("");
    setCycle(0);
    setStartTime(defaultStart());
    setMeta({});
    setErrors({});
    onResetResult?.(); // also clear the right-side result -> empty state
  };

  const remaining = Math.max(0, 70 - cycle);
  const sev = remaining > 20 ? "ok" : remaining > 5 ? "warn" : "danger";
  const sevLabel =
    remaining > 20 ? "Plenty of cycle left" : remaining > 5 ? "Cycle running low" : "Cycle nearly used";

  return (
    <form className="card" onSubmit={submit} noValidate>
      <div className="card-head">
        <span className="head-badge">
          <RouteIcon size={18} />
        </span>
        <div>
          <h2>Plan a trip</h2>
          <div className="sub">Route &amp; current cycle usage</div>
        </div>
      </div>
      <div className="card-body">
        <div className="section-label">
          <RouteIcon size={14} /> Route
        </div>
        <div className="route-inputs">
          <LocationInput
            label="Current location"
            tone="start"
            value={currentLocation}
            placeholder="e.g. Chicago, IL"
            error={errors.currentLocation}
            onChange={setCurrent}
          />
          <LocationInput
            label="Pickup location"
            tone="pickup"
            value={pickupLocation}
            placeholder="e.g. St. Louis, MO"
            error={errors.pickupLocation}
            onChange={setPickup}
          />
          <LocationInput
            label="Dropoff location"
            tone="dropoff"
            value={dropoffLocation}
            placeholder="e.g. Dallas, TX"
            error={errors.dropoffLocation}
            onChange={setDropoff}
          />
        </div>

        <div className="field">
          <label htmlFor="cycle" className="section-label" style={{ marginBottom: 8 }}>
            <GaugeIcon size={14} /> Current cycle used <span className="hint">· 70 hr / 8 day</span>
          </label>
          <div className="hos-gauge">
            <div className="gauge-top">
              <span className="gauge-value">
                {cycle.toFixed(1)}
                <small> / 70 hr</small>
              </span>
              <span className={`gauge-chip ${sev}`}>
                <strong>{remaining.toFixed(1)} h</strong> available
              </span>
            </div>
            <input
              id="cycle"
              className="gauge-slider"
              type="range"
              min={0}
              max={70}
              step={0.5}
              value={cycle}
              onChange={(e) => setCycle(Number(e.target.value))}
            />
            <div className="gauge-ticks">
              <span>0</span>
              <span className={`gauge-status ${sev}`}>{sevLabel}</span>
              <span>70 hr</span>
            </div>
          </div>
        </div>

        <div className="field">
          <label htmlFor="start" className="section-label" style={{ marginBottom: 8 }}>
            <ClockIcon size={14} /> Trip start <span className="hint">· home-terminal time</span>
          </label>
          <input
            id="start"
            type="datetime-local"
            className="input"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </div>

        <details className="details-section">
          <summary>
            Driver &amp; carrier details <span className="hint">(optional · shown on the log)</span>
          </summary>
          <div className="details-grid">
            <MetaField label="Driver name" value={meta.driverName ?? ""} onChange={setMetaField("driverName")} />
            <MetaField label="Co-driver" value={meta.coDriverName ?? ""} onChange={setMetaField("coDriverName")} />
            <MetaField label="Carrier name" value={meta.carrierName ?? ""} onChange={setMetaField("carrierName")} />
            <MetaField label="Main office address" value={meta.mainOfficeAddress ?? ""} onChange={setMetaField("mainOfficeAddress")} />
            <MetaField label="Vehicle / trailer no." value={meta.vehicleNumbers ?? ""} onChange={setMetaField("vehicleNumbers")} />
            <MetaField label="Home time zone" value={meta.homeTimezone ?? ""} placeholder="e.g. CST" onChange={setMetaField("homeTimezone")} />
            <MetaField label="Shipping doc no." value={meta.shippingDocNumber ?? ""} onChange={setMetaField("shippingDocNumber")} />
            <MetaField label="Shipper & commodity" value={meta.shipperCommodity ?? ""} onChange={setMetaField("shipperCommodity")} />
          </div>
        </details>

        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <span className="spinner" /> Planning route…
            </>
          ) : (
            <>
              <TruckIcon size={18} /> Plan trip &amp; build logs
            </>
          )}
        </button>
        <div className="btn-row">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={resetForm}
            disabled={isSubmitting}
          >
            <PlusIcon size={14} /> New trip
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={fillSample}
            disabled={isSubmitting}
          >
            <SparkleIcon size={14} /> Try a sample
          </button>
        </div>
      </div>
    </form>
  );
}
