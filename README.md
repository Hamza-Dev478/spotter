# ELD Trip Planner

Plan a property-carrying truck trip and get back **two things**:

1. A **map** of the route with markers for the pickup, dropoff, fuel stops and the FMCSA-required rest breaks.
2. A set of **filled-out FMCSA Driver's Daily Log sheets** (one per day) with the duty-status line drawn on the 24-hour grid.

Given a current location, pickup, dropoff and how many hours of the 70-hour / 8-day cycle the driver has already used, the app computes a fully **Hours-of-Service compliant** schedule (11h driving limit, 14h window, 30-minute break, 10h resets, 70/8 cycle, 34h restart, fueling every 1,000 miles, 1h pickup/dropoff).

| | |
|---|---|
| **Live app** | https://spotter-vert.vercel.app |
| **API** | https://eld-trip-planner-api-3dxh.onrender.com |
| **Demo video** | _Loom URL here_ |

---

## Features

- **Connected route input:** start → pickup → dropoff timeline with address autocomplete (OpenStreetMap Nominatim) and a live Hours-of-Service cycle gauge.
- **Free, keyless map & routing:** Leaflet + OpenStreetMap with real road distance/time from OSRM, all proxied through the API (no secrets, nothing to configure).
- **FMCSA-audited HOS engine:** pure-Python, deterministic; splits the trip into duty segments across multiple days. Validated rule-by-rule against the official §395 guide.
- **Hand-drawn SVG daily-log sheets:** one page per calendar day, each totalling exactly 24h, with City/State remarks at every duty change, the certification line, and carrier / driver / vehicle / shipping fields.
- **Export** to **PDF** (one page/day) or **PNG**, plus browser print.
- **Trip history:** auto-saved; click a trip to **reload it into the form and replay its result**; **duplicate**, **delete**, **clear-all**, and **paginated**.
- Polished, responsive, accessible UI with independent-scrolling columns and loading/error states.

## Quick start

Requires **Python 3.11+** and **Node 18+** (the frontend uses Vite 8 / React 18). With the included [`Makefile`](Makefile):

```bash
make install     # backend venv + deps + migrate, and frontend deps
make dev         # runs Django (:8000) and Vite (:5173) together
```

Then open http://localhost:5173. Run `make help` to see all targets (`test`, `build`, `migrate`, `clean`, …).

<details>
<summary>Manual setup (without make)</summary>

```bash
# Backend (http://localhost:8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (http://localhost:5173), in a second terminal
cd frontend
npm install
npm run dev
```
</details>

The frontend talks to `http://localhost:8000` by default; override with `VITE_API_URL`.

## How the Hours-of-Service rules are applied

Property-carrying driver, 70 hr / 8 day, no adverse conditions (per the assessment):

| Rule | Implementation |
|---|---|
| 11-hour driving limit | A new driving chunk can never push daily driving past 11h before a 10h reset. |
| 14-hour window | Driving stops at the 14th hour after coming on duty; breaks don't extend it. |
| 30-minute break | Inserted after 8 cumulative hours of driving (satisfied by any ≥30-min non-driving period). |
| 10-hour reset | A 10h off-duty block resets the 11h and 14h clocks. |
| 70-hour / 8-day | On-duty time accrues toward the 70h cap. |
| 34-hour restart | When the cycle is exhausted mid-trip, a 34h off-duty restart is inserted. |
| Fueling | A 15-min on-duty fuel stop at least every 1,000 miles. |
| Pickup / dropoff | 1 hour on-duty at each. |

The engine lives in [`backend/domain/services/hos_scheduler.py`](backend/domain/services/hos_scheduler.py) and is pure Python (no Django, no I/O), so it is fully unit-tested.

## Architecture (Clean Architecture)

Dependencies point **inward**: `domain ← application ← {interface_adapters, infrastructure}`.
The domain knows nothing about Django, HTTP or OSRM; those are swappable details.

```
backend/
  domain/             Pure business logic (entities + HOS engine). No framework imports.
    models/           LatLng, Trip/Route, DutyStatus/HOSState/Segment
    services/         hos_scheduler.py (the algorithm), log_builder.py, geo.py
  application/         Use cases + abstract interfaces (ports)
    use_cases/         plan_trip.py  (geocode → route → schedule → enrich → assemble)
    interfaces/        IGeocodingService, IRoutingService, ITripRepository
  infrastructure/      Concrete adapters (Django, requests, OSRM, Nominatim, ORM)
    geocoding/  routing/  persistence/  factory.py  cache.py
  interface_adapters/  DRF serializers + views (the HTTP boundary)
  config/              Django settings/urls/wsgi
  tests/               unit (pure) · integration (fakes) · e2e (DRF + DB)

frontend/
  src/
    api/         axios client + typed endpoints
    hooks/       useTripPlanner, useAddressSuggest, useTripHistory
    lib/         logGeometry.ts (SVG math), format.ts, dutyStatus.ts
    components/  TripForm/ · Map/ · LogSheet/ · History/ · results/ · icons.tsx
```

## Tech stack

**Backend** Django 5 · Django REST Framework · requests · gunicorn · WhiteNoise · Postgres (SQLite locally).
**Frontend** React 18 · TypeScript · Vite · Leaflet / react-leaflet · TanStack Query · axios · html2canvas + jsPDF.
**Maps** OpenStreetMap tiles · OSRM (routing) · Nominatim (geocoding), all free and keyless.

## Tests

```bash
make test              # backend pytest + frontend vitest + type-check/build
make test-backend      # cd backend && pytest        (unit · integration · e2e)
make test-frontend     # cd frontend && npm run test  (vitest) + npm run build
```

The backend suite proves the HOS rules: limits are never exceeded, every daily log totals 24h, multi-day trips split correctly, fuel/pickup/dropoff are on-duty, and the 34h restart fires before the 70h cap. The frontend suite covers the pure SVG/format helpers.

## API

All external calls (OSRM/Nominatim) happen server-side; the frontend only ever calls this API.

| Method | Path | Purpose |
|---|---|---|
| `POST`   | `/api/v1/trips/plan/` | Plan a trip → route + stops + daily logs (and persist it) |
| `GET`    | `/api/v1/geocode/?q=` | Address autocomplete suggestions |
| `GET`    | `/api/v1/trips/?limit=&offset=` | Paginated recent trips → `{ trips, total }` |
| `GET`    | `/api/v1/trips/{id}/` | Full stored trip → `{ request, result }` |
| `DELETE` | `/api/v1/trips/{id}/` | Delete one trip |
| `DELETE` | `/api/v1/trips/` | Clear all trips |
| `GET`    | `/api/v1/health/` | Liveness probe |

<details>
<summary>Example <code>POST /api/v1/trips/plan/</code></summary>

```json
{
  "currentLocation": "Chicago, IL",
  "pickupLocation": "St. Louis, MO",
  "dropoffLocation": "Dallas, TX",
  "currentCycleUsedHrs": 12.5,
  "startTime": "2026-06-12T06:00:00Z",
  "logMeta": { "carrierName": "Acme Freight", "driverName": "Jane Doe" }
}
```

Returns `{ summary, route, stops, dailyLogs, logMeta }` where `dailyLogs[].segments` is exactly what the SVG log renderer consumes. `logMeta` is optional, presentation-only data echoed back onto the log sheets.
</details>

## Deployment

- **Frontend → Vercel.** Import the repo, set the project **Root Directory** to `frontend/`, add `VITE_API_URL` = your Render URL. (`frontend/vercel.json` handles the rest.)
- **Backend → Render.** Use the included [`render.yaml`](render.yaml) blueprint (Django web service + free Postgres). After the frontend is live, set `CORS_ALLOWED_ORIGINS` to its URL. Any `*.vercel.app` origin is allowed automatically for preview deploys.

## Modeling simplifications (intentional, FMCSA-conservative)

The HOS engine was audited rule-by-rule against the official FMCSA §395 guide and is compliant. A few
deliberate simplifications are worth calling out, and each is **conservative** (it can only require *more*
rest than the law, never permit an illegal drive):

- **70-hour cycle as a single bucket, not a rolling 8-day window** (§395.3(b)). The only cycle input is
  one scalar `currentCycleUsedHrs`, so the true "oldest day's hours drop off" recovery can't be
  reconstructed. We accumulate on-duty time toward 70h and insert a 34-hour restart when it's reached.
  This is conservative, and exact for trips that don't span a full 8 days.
- **Required rest is one ≥10-hour off-duty block** (§395.3(a)(1)); the §395.1(g) sleeper-berth split
  provisions (7/3, 8/2) are not modeled, which is the simplest compliant option, so the "Sleeper Berth"
  log row stays empty.
- **30-minute breaks are modeled as off-duty**, so they don't count toward the 70h on-duty cycle, which
  is correct since the cap is on-duty time only.
- **Excluded by the assessment's assumptions:** the adverse-driving-conditions exception (§395.1(b)(1))
  and the short-haul exceptions (§395.1(e)) are intentionally not applied.
- Single pickup and single dropoff; trip order is current → pickup → dropoff. Drive time comes from
  OSRM's real road duration; OSRM/Nominatim responses are cached server-side (1h) to respect the public
  demo servers' rate limits.
