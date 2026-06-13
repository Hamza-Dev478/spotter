import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { suggestAddress } from "../api/tripApi";

/** Debounce a fast-changing value so we don't hit the geocoder on every keypress. */
function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}

export function useAddressSuggest(query: string, enabled: boolean) {
  const debounced = useDebounced(query, 350);
  return useQuery({
    queryKey: ["suggest", debounced],
    queryFn: () => suggestAddress(debounced),
    enabled: enabled && debounced.trim().length >= 3,
    staleTime: 5 * 60 * 1000,
  });
}
