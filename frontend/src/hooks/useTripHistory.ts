import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { fetchHistory } from "../api/tripApi";

export function useTripHistory(page: number, pageSize: number) {
  return useQuery({
    queryKey: ["history", page, pageSize],
    queryFn: () => fetchHistory(pageSize, page * pageSize),
    staleTime: 15 * 1000,
    placeholderData: keepPreviousData, // keep the current page visible while the next loads
  });
}
