import type { AgentKey } from "./types";

/** Each agent is a different apple. Colours are picked so the five read apart
 *  at a glance, even in peripheral vision while a run is moving. */
export interface AgentSkin {
  key: AgentKey;
  role: string;
  variety: string;
  body: [string, string];
  shine: string;
  leaf: string;
  accent: string;
}

export const AGENTS: AgentSkin[] = [
  {
    key: "boss",
    role: "Boss",
    variety: "Red Delicious",
    body: ["#ff5f6d", "#b4172c"],
    shine: "rgba(255,255,255,.75)",
    leaf: "#2fa360",
    accent: "#ff5f6d",
  },
  {
    key: "inventory",
    role: "Inventory",
    variety: "Granny Smith",
    body: ["#b8e986", "#4a9c2d"],
    shine: "rgba(255,255,255,.7)",
    leaf: "#2b8c52",
    accent: "#6fc53f",
  },
  {
    key: "accounting",
    role: "Accounting",
    variety: "Golden Delicious",
    body: ["#ffd86b", "#d99b1c"],
    shine: "rgba(255,255,255,.8)",
    leaf: "#3a9a5c",
    accent: "#f0b429",
  },
  {
    key: "facilities",
    role: "Facilities",
    variety: "Fuji",
    body: ["#ffb4a8", "#c96a7a"],
    shine: "rgba(255,255,255,.75)",
    leaf: "#35965b",
    accent: "#e8869a",
  },
  {
    key: "customer_service",
    role: "Customer Service",
    variety: "Honeycrisp",
    body: ["#ffc9d4", "#e0526b"],
    shine: "rgba(255,255,255,.8)",
    leaf: "#2f9a62",
    accent: "#ff7d95",
  },
];

export const AGENT_BY_KEY = Object.fromEntries(
  AGENTS.map((a) => [a.key, a]),
) as Record<AgentKey, AgentSkin>;

/** Tool names are snake_case on the wire; the desk says them in English. */
export const TOOL_LABELS: Record<string, string> = {
  list_open_tickets: "reading the board",
  check_stock: "counting stock",
  check_vendor_can_ship: "checking the vendor",
  list_money_due: "checking what's owed",
  quote_discount: "pricing the discount",
  list_payment_requests: "checking pending payments",
  request_payment: "raising a payment request",
  resolve_ticket: "closing the ticket",
  save_draft_message: "drafting to the customer",
  update_inventory: "adjusting stock",
};
