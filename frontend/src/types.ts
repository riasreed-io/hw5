export type AgentKey =
  | "boss"
  | "inventory"
  | "accounting"
  | "facilities"
  | "customer_service";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  inventory_for_requested_size?: { qty: number; name: string } | null;
  lease?: { monthly_rent: number; next_due: string } | null;
  invoice?: { amount: number; due_date: string; status: string } | null;
}

export interface Board {
  date_today: string;
  count: number;
  open: number;
  resolved: number;
  tickets: Ticket[];
}

export interface Cash {
  account: string;
  balance: number;
  date_today: string;
  pending_total: number;
  cash_if_all_pending_approved: number;
}

export interface PaymentRequest {
  id: number;
  kind: string;
  ref_id: number;
  amount: number;
  reason: string;
  requested_by: string;
  status: string;
  payee: string | null;
}

export interface PaymentsResponse {
  count: number;
  requests: PaymentRequest[];
  pending_total: number;
  cash_available: number;
}

export interface TrailEvent {
  ts: string;
  run_id: string;
  event: string;
  agent?: string;
  frm?: string;
  to?: string;
  tool?: string;
  args?: string;
  result?: string;
  question?: string;
  findings?: string;
  recommendation?: string;
  blocked_by?: string;
  ticket_id?: number;
  depth?: number;
  decision?: string;
  reasoning?: string;
  resolved?: boolean;
  awaiting_human?: string;
  total_tokens?: number;
  delegated_to?: string[];
  open_tickets?: number[];
  reason?: string;
  request_id?: number;
  actor?: string;
}

export interface RunResult {
  run_id: string;
  ticket_id: number;
  decision: {
    ticket_id: number;
    decision: string;
    reasoning: string;
    delegated_to: string[];
    payment_requests: number[];
    resolved: boolean;
    awaiting_human: string;
  };
  usage: { requests: number; total_tokens: number };
}
