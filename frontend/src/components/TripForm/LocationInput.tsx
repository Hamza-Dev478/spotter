import { useId, useRef, useState } from "react";
import { useAddressSuggest } from "../../hooks/useAddressSuggest";
import { PinIcon } from "../icons";
import type { Suggestion } from "../../types/trip";

type Tone = "start" | "pickup" | "dropoff";

const TONE_COLOR: Record<Tone, string> = {
  start: "#2563eb",
  pickup: "#16a34a",
  dropoff: "#dc2626",
};

interface Props {
  label: string;
  tone: Tone;
  value: string;
  placeholder?: string;
  error?: string;
  onChange: (value: string) => void;
}

export function LocationInput({ label, tone, value, placeholder, error, onChange }: Props) {
  const id = useId();
  const [focused, setFocused] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const blurTimer = useRef<number | undefined>(undefined);

  const { data: suggestions = [], isFetching } = useAddressSuggest(value, focused);
  const open = focused && value.trim().length >= 3;

  const choose = (s: Suggestion) => {
    onChange(s.label);
    setFocused(false);
    setActiveIdx(-1);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!open || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && activeIdx >= 0) {
      e.preventDefault();
      choose(suggestions[activeIdx]);
    } else if (e.key === "Escape") {
      setFocused(false);
    }
  };

  return (
    <div className="route-field">
      <div className="route-rail" aria-hidden>
        <span className={`route-node node-${tone}${focused ? " is-focused" : ""}`}>
          <PinIcon color={TONE_COLOR[tone]} size={15} />
        </span>
      </div>
      <div className="route-main suggest-wrap">
        <label className="route-label" htmlFor={id}>
          {label}
        </label>
        <input
          id={id}
          className={`input${error ? " invalid" : ""}`}
          value={value}
          placeholder={placeholder}
          autoComplete="off"
          aria-invalid={!!error}
          onChange={(e) => {
            onChange(e.target.value);
            setActiveIdx(-1);
          }}
          onFocus={() => {
            window.clearTimeout(blurTimer.current);
            setFocused(true);
          }}
          onBlur={() => {
            blurTimer.current = window.setTimeout(() => setFocused(false), 150);
          }}
          onKeyDown={onKeyDown}
        />
        {error && <div className="error-text">{error}</div>}
        {open && (
          <div className="suggest-menu" role="listbox">
            {suggestions.length === 0 ? (
              <div className="suggest-empty">{isFetching ? "Searching…" : "No matches"}</div>
            ) : (
              suggestions.map((s, i) => (
                <div
                  key={`${s.lat},${s.lon},${i}`}
                  role="option"
                  aria-selected={i === activeIdx}
                  className={`suggest-item${i === activeIdx ? " active" : ""}`}
                  onMouseEnter={() => setActiveIdx(i)}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    choose(s);
                  }}
                >
                  <PinIcon color={TONE_COLOR[tone]} size={13} />
                  <span>{s.label}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
