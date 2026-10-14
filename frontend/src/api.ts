import type { Board, Cash, PaymentsResponse, RunResult, TrailEvent } from "./types";

// The FastAPI backend from Problem 7. Override with VITE_API_BASE if it is
// running somewhere else.
export const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as { detail?: string }).detail ?? res.statusText);
  return data as T;
}

export const api = {
  health: () => get<{ ok: boolean; model: string; approver_on_record: string }>("/api/health"),
  tickets: () => get<Board>("/api/tickets"),
  cash: () => get<Cash>("/api/cash"),
  payments: () => get<PaymentsResponse>("/api/payments?status=pending"),
  events: (limit = 400) => get<{ events: TrailEvent[] }>(`/api/events?limit=${limit}`),
  runTicket: (id: number) => post<RunResult>(`/api/tickets/${id}/run`),
  approve: (requestId: number, approvedBy: string) =>
    post<{ ok: boolean; amount_paid: number; cash_after: number }>(
      `/api/payments/${requestId}/approve`,
      { approved_by: approvedBy },
    ),
  reset: () => post<{ reset: boolean }>("/api/reset"),
};
