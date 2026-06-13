export const fmtMiles = (m: number): string => `${Math.round(m).toLocaleString()} mi`;

export const fmtHours = (h: number): string => {
  const whole = Math.floor(h);
  const mins = Math.round((h - whole) * 60);
  if (mins === 0) return `${whole} hr`;
  return `${whole}h ${mins}m`;
};

/** Decimal day-hour (e.g. 9.5) -> "09:30". */
export const hoursToClock = (h: number): string => {
  const total = Math.round(h * 60);
  const hh = Math.floor(total / 60) % 24;
  const mm = total % 60;
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
};

export const fmtDateLong = (dateStr: string): string => {
  // dateStr is "YYYY-MM-DD"; parse as local to avoid TZ drift on the label.
  const [y, m, d] = dateStr.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export const fmtDateTime = (iso: string): string =>
  new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

const US_STATES: Record<string, string> = {
  alabama: "AL", alaska: "AK", arizona: "AZ", arkansas: "AR", california: "CA",
  colorado: "CO", connecticut: "CT", delaware: "DE", florida: "FL", georgia: "GA",
  hawaii: "HI", idaho: "ID", illinois: "IL", indiana: "IN", iowa: "IA", kansas: "KS",
  kentucky: "KY", louisiana: "LA", maine: "ME", maryland: "MD", massachusetts: "MA",
  michigan: "MI", minnesota: "MN", mississippi: "MS", missouri: "MO", montana: "MT",
  nebraska: "NE", nevada: "NV", "new hampshire": "NH", "new jersey": "NJ",
  "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND",
  ohio: "OH", oklahoma: "OK", oregon: "OR", pennsylvania: "PA", "rhode island": "RI",
  "south carolina": "SC", "south dakota": "SD", tennessee: "TN", texas: "TX", utah: "UT",
  vermont: "VT", virginia: "VA", washington: "WA", "west virginia": "WV",
  wisconsin: "WI", wyoming: "WY", "district of columbia": "DC",
};

/** Turn a long display name ("Denver, Colorado, United States") into "Denver, CO". */
export const shortenLocation = (label: string): string => {
  const parts = (label || "").split(",").map((p) => p.trim()).filter(Boolean);
  if (parts.length === 0) return label;
  const city = parts[0];
  for (const part of parts.slice(1)) {
    if (/^[A-Z]{2}$/.test(part)) return `${city}, ${part}`; // already an abbrev (e.g. "MO")
    const abbr = US_STATES[part.toLowerCase()];
    if (abbr) return `${city}, ${abbr}`;
  }
  return parts.length > 1 ? `${city}, ${parts[1]}` : city;
};
