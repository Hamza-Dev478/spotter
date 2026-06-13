import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useTripPlanner } from "./hooks/useTripPlanner";
import { errorMessage } from "./api/client";
import { TripForm } from "./components/TripForm/TripForm";
import { TripHistoryList } from "./components/History/TripHistoryList";
import { MapView } from "./components/Map/MapView";
import { TripSummary } from "./components/results/TripSummary";
import { DailyLogs } from "./components/LogSheet/DailyLogs";
import type { TripInput, TripPlan } from "./types/trip";

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="es-icon">🚛</div>
      <h2>Plan a Hours-of-Service compliant trip</h2>
      <p>
        Enter your current location, pickup and dropoff, and how much of your 70-hour / 8-day cycle
        you&apos;ve already used. We&apos;ll route the trip and draw the FMCSA daily log sheets for
        you.
      </p>
      <ol>
        <li>Map with the route, fuel stops and required rest breaks</li>
        <li>One filled-out daily log sheet per day, with the 11h / 14h / 30-min rules applied</li>
        <li>Download the logs as PDF or PNG</li>
      </ol>
    </div>
  );
}

export default function App() {
  const queryClient = useQueryClient();
  const planner = useTripPlanner();
  const [plan, setPlan] = useState<TripPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  // prefill + formKey let a tapped history trip repopulate the form (remount).
  const [prefill, setPrefill] = useState<Partial<TripInput> | undefined>(undefined);
  const [formKey, setFormKey] = useState(0);

  const handleSubmit = (input: TripInput) => {
    setError(null);
    planner.mutate(input, {
      onSuccess: (data) => {
        setPlan(data);
        queryClient.invalidateQueries({ queryKey: ["history"] });
      },
      onError: (err) => setError(errorMessage(err)),
    });
  };

  // Tap a recent trip: fill the form with its inputs AND show its saved result.
  const loadTrip = (request: TripInput, result: TripPlan) => {
    setError(null);
    setPrefill(request);
    setFormKey((k) => k + 1);
    setPlan(result);
  };

  // Duplicate: fill the form and immediately re-plan a fresh copy.
  const duplicateTrip = (request: TripInput) => {
    setPrefill(request);
    setFormKey((k) => k + 1);
    handleSubmit(request);
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand-mark" aria-hidden>
          🚚
        </div>
        <div className="brand-text">
          <h1>ELD Trip Planner</h1>
          <p>Route &amp; FMCSA Hours-of-Service daily logs</p>
        </div>
        <div className="spacer" />
        <span className="pill">Property-carrying · 70 hr / 8 day</span>
      </header>

      <main className="layout">
        <aside className="sidebar">
          <TripForm
            key={formKey}
            prefill={prefill}
            onSubmit={handleSubmit}
            isSubmitting={planner.isPending}
            onResetResult={() => {
              setPlan(null);
              setError(null);
            }}
          />
          <TripHistoryList onOpen={loadTrip} onDuplicate={duplicateTrip} />
        </aside>

        <section className="content">
          {error && (
            <div className="alert" role="alert">
              <span aria-hidden>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {planner.isPending && !plan ? (
            <div className="card">
              <div className="loading-overlay">
                <span className="spinner dark" /> Routing your trip and building log sheets…
              </div>
            </div>
          ) : plan ? (
            <>
              <TripSummary summary={plan.summary} />
              <MapView plan={plan} />
              <DailyLogs logs={plan.dailyLogs} meta={plan.logMeta} />
            </>
          ) : (
            <EmptyState />
          )}
        </section>
      </main>
    </div>
  );
}
