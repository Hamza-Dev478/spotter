import { useMutation } from "@tanstack/react-query";
import { planTrip } from "../api/tripApi";
import type { TripInput, TripPlan } from "../types/trip";

export function useTripPlanner() {
  return useMutation<TripPlan, unknown, TripInput>({
    mutationFn: planTrip,
  });
}
