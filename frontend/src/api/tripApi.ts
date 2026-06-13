import { api } from "./client";
import type { Suggestion, TripHistoryItem, TripInput, TripPlan } from "../types/trip";

export async function planTrip(input: TripInput): Promise<TripPlan> {
  const { data } = await api.post<TripPlan>("/trips/plan/", input);
  return data;
}

export async function suggestAddress(query: string): Promise<Suggestion[]> {
  if (query.trim().length < 3) return [];
  const { data } = await api.get<{ suggestions: Suggestion[] }>("/geocode/", {
    params: { q: query },
  });
  return data.suggestions;
}

export interface HistoryPage {
  trips: TripHistoryItem[];
  total: number;
}

export async function fetchHistory(limit: number, offset: number): Promise<HistoryPage> {
  const { data } = await api.get<HistoryPage>("/trips/", { params: { limit, offset } });
  return data;
}

export async function fetchTrip(id: number): Promise<{ request: TripInput; result: TripPlan }> {
  const { data } = await api.get<{ request: TripInput; result: TripPlan }>(`/trips/${id}/`);
  return { request: data.request, result: data.result };
}

export async function deleteTrip(id: number): Promise<void> {
  await api.delete(`/trips/${id}/`);
}

export async function clearHistory(): Promise<void> {
  await api.delete("/trips/");
}
