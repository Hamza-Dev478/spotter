import axios from "axios";

// Frontend only ever talks to the Django API — never to OSRM/Nominatim directly.
const root = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const api = axios.create({
  baseURL: `${root}/api/v1`,
  timeout: 35000,
  headers: { "Content-Type": "application/json" },
});

/** Pull a human-readable message out of a DRF error response. */
export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as Record<string, unknown> | undefined;
    if (data) {
      if (typeof data.error === "string") return data.error;
      // DRF field errors: { fieldName: ["msg", ...] }
      const first = Object.values(data)[0];
      if (Array.isArray(first) && typeof first[0] === "string") return first[0];
    }
    if (err.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (!err.response) return "Cannot reach the server. Is the backend running?";
    return `Request failed (${err.response.status}).`;
  }
  return "Something went wrong. Please try again.";
}
