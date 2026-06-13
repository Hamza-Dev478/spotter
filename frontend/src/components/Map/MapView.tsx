import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import L, { type LatLngBoundsExpression, type LatLngExpression } from "leaflet";
import type { TripPlan } from "../../types/trip";
import { STOP_META } from "../../lib/dutyStatus";
import { fmtMiles } from "../../lib/format";

function stopIcon(color: string, glyph: string): L.DivIcon {
  return L.divIcon({
    className: "eld-stop-icon",
    html: `<div style="display:grid;place-items:center;width:26px;height:26px;border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);background:${color};border:2px solid #fff;
      box-shadow:0 2px 6px rgba(0,0,0,.35);font-size:12px">
      <span style="transform:rotate(45deg)">${glyph}</span></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 24],
    tooltipAnchor: [0, -20],
  });
}

function FitBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [42, 42] });
  }, [bounds, map]);
  return null;
}

export function MapView({ plan }: { plan: TripPlan }) {
  const line: LatLngExpression[] = useMemo(
    () => plan.route.geometry.coordinates.map(([lon, lat]) => [lat, lon]),
    [plan],
  );

  const bounds = useMemo<LatLngBoundsExpression | null>(
    () => (line.length ? (line as [number, number][]) : null),
    [line],
  );

  const center: LatLngExpression = line.length
    ? (line[Math.floor(line.length / 2)] as LatLngExpression)
    : [39.5, -98.35];

  return (
    <div className="card map-card">
      <div className="map-shell">
        <MapContainer center={center} zoom={5} scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {line.length > 1 && (
            <Polyline positions={line} pathOptions={{ color: "#4338ca", weight: 5, opacity: 0.85 }} />
          )}
          {plan.stops.map((stop, i) => {
            const meta = STOP_META[stop.type];
            return (
              <Marker key={i} position={[stop.lat, stop.lon]} icon={stopIcon(meta.color, meta.glyph)}>
                <Tooltip direction="top">
                  <strong>{meta.label}</strong>
                  <br />
                  {stop.label}
                  <br />
                  <span style={{ color: "#64748b" }}>{fmtMiles(stop.atMile)} in</span>
                </Tooltip>
              </Marker>
            );
          })}
          <FitBounds bounds={bounds} />
        </MapContainer>
      </div>
      <div className="map-legend">
        {(["start", "pickup", "fuel", "rest", "dropoff"] as const).map((t) => (
          <span className="lg" key={t}>
            <span className="dot" style={{ background: STOP_META[t].color }} />
            {STOP_META[t].label}
          </span>
        ))}
      </div>
    </div>
  );
}
