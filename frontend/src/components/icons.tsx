// Small inline SVG icon set — crisp and consistent across platforms (unlike emoji).

type IconProps = { size?: number; className?: string };

const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function PinIcon({ color = "#2563eb", size = 16 }: { color?: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 22s7-6.6 7-12a7 7 0 1 0-14 0c0 5.4 7 12 7 12Z"
        fill={color}
        stroke="#ffffff"
        strokeWidth="1.5"
      />
      <circle cx="12" cy="10" r="2.6" fill="#ffffff" />
    </svg>
  );
}

export function RouteIcon({ size = 18, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <circle cx="6" cy="19" r="2.2" />
      <circle cx="18" cy="5" r="2.2" />
      <path d="M8 19h7a4 4 0 0 0 0-8H9a4 4 0 0 1 0-8h3" />
    </svg>
  );
}

export function ClockIcon({ size = 16, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  );
}

export function GaugeIcon({ size = 16, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <path d="M3.6 15a9 9 0 1 1 16.8 0" />
      <path d="M12 13l3.2-3.2" />
    </svg>
  );
}

export function TruckIcon({ size = 18, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <path d="M3 6.5h11v9H3z" />
      <path d="M14 9.5h3.6l3.4 3.4v2.6H14z" />
      <circle cx="7" cy="18" r="1.7" />
      <circle cx="17.5" cy="18" r="1.7" />
    </svg>
  );
}

export function CopyIcon({ size = 15, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <rect x="9" y="9" width="11" height="11" rx="2" />
      <path d="M5 15V5a2 2 0 0 1 2-2h10" />
    </svg>
  );
}

export function TrashIcon({ size = 15, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <path d="M4 7h16M9 7V5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 5v2M6 7l1 12.5A1.5 1.5 0 0 0 8.5 21h7a1.5 1.5 0 0 0 1.5-1.5L18 7" />
    </svg>
  );
}

export function ChevronIcon({ size = 16, className, dir = "left" }: IconProps & { dir?: "left" | "right" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <path d={dir === "left" ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7"} />
    </svg>
  );
}

export function PlusIcon({ size = 15, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...stroke} className={className} aria-hidden>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function SparkleIcon({ size = 15, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <path d="M12 2.5l1.7 4.8 4.8 1.7-4.8 1.7L12 15.5l-1.7-4.8L5.5 9l4.8-1.7L12 2.5z" />
      <path d="M19 14l.8 2.2 2.2.8-2.2.8L19 20l-.8-2.2-2.2-.8 2.2-.8L19 14z" />
    </svg>
  );
}
