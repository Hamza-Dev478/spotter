import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useTripHistory } from "../../hooks/useTripHistory";
import { clearHistory, deleteTrip, fetchTrip } from "../../api/tripApi";
import { fmtDateTime, fmtMiles, shortenLocation } from "../../lib/format";
import { ChevronIcon, ClockIcon, CopyIcon, TrashIcon } from "../icons";
import type { TripInput, TripPlan } from "../../types/trip";

const PAGE_SIZE = 5;

interface Props {
  onOpen: (request: TripInput, result: TripPlan) => void;
  onDuplicate: (request: TripInput) => void;
}

export function TripHistoryList({ onOpen, onDuplicate }: Props) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [busyId, setBusyId] = useState<number | null>(null);
  const { data, isLoading } = useTripHistory(page, PAGE_SIZE);

  const trips = data?.trips ?? [];
  const total = data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["history"] });

  const open = async (id: number) => {
    setBusyId(id);
    try {
      const { request, result } = await fetchTrip(id);
      onOpen(request, result);
    } finally {
      setBusyId(null);
    }
  };

  const duplicate = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    const { request } = await fetchTrip(id);
    onDuplicate(request);
  };

  const remove = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    await deleteTrip(id);
    if (trips.length === 1 && page > 0) setPage((p) => p - 1); // step back if page emptied
    invalidate();
  };

  const clearAll = async () => {
    if (!window.confirm("Clear all saved trips? This cannot be undone.")) return;
    await clearHistory();
    setPage(0);
    invalidate();
  };

  return (
    <div className="card">
      <div className="card-head">
        <span className="head-badge">
          <ClockIcon size={17} />
        </span>
        <div>
          <h2>Recent trips</h2>
          <div className="sub">{total > 0 ? `${total} saved automatically` : "Saved automatically"}</div>
        </div>
        <div style={{ flex: 1 }} />
        {total > 0 && (
          <button className="link-btn" onClick={clearAll}>
            Clear all
          </button>
        )}
      </div>
      <div className="card-body">
        {isLoading ? (
          <div className="history-empty">Loading…</div>
        ) : trips.length === 0 ? (
          <div className="history-empty">No trips yet — plan one above.</div>
        ) : (
          <>
            <div className="history-list">
              {trips.map((t) => (
                <div
                  key={t.id}
                  className="history-item"
                  role="button"
                  tabIndex={0}
                  aria-busy={busyId === t.id}
                  onClick={() => open(t.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      open(t.id);
                    }
                  }}
                >
                  <div className="hi-main">
                    <div className="route">
                      {shortenLocation(t.currentLocation)} <span className="arrow">→</span>{" "}
                      {shortenLocation(t.dropoffLocation)}
                    </div>
                    <div className="meta">
                      <span>{fmtMiles(t.totalMiles)}</span>
                      <span>
                        {t.days} day{t.days === 1 ? "" : "s"}
                      </span>
                      <span>{fmtDateTime(t.createdAt)}</span>
                    </div>
                  </div>
                  <div className="history-actions">
                    <button
                      className="hi-act"
                      title="Duplicate &amp; re-plan"
                      aria-label="Duplicate and re-plan this trip"
                      onClick={(e) => duplicate(e, t.id)}
                    >
                      <CopyIcon size={14} />
                    </button>
                    <button
                      className="hi-act danger"
                      title="Delete"
                      aria-label="Delete this trip"
                      onClick={(e) => remove(e, t.id)}
                    >
                      <TrashIcon size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {pages > 1 && (
              <div className="pager">
                <button
                  className="pager-btn"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  aria-label="Previous page"
                >
                  <ChevronIcon dir="left" size={15} />
                </button>
                <span className="pager-info">
                  Page {page + 1} of {pages}
                </span>
                <button
                  className="pager-btn"
                  disabled={page >= pages - 1}
                  onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
                  aria-label="Next page"
                >
                  <ChevronIcon dir="right" size={15} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
