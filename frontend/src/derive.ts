import { AGENTS, TOOL_LABELS } from "./agents";
import type { SeatData } from "./components/AgentSeat";
import type { AgentKey, TrailEvent } from "./types";

const RESTING: Record<AgentKey, string> = {
  boss: "Waiting for a ticket to land on the board.",
  inventory: "Shelves counted. Nothing to check right now.",
  accounting: "Ledger quiet. No numbers requested.",
  facilities: "Lease filed. Nothing due on my desk.",
  customer_service: "No one to write to yet.",
};

/** Turn the raw audit trail into what each apple is doing and saying. */
export function deriveSeats(events: TrailEvent[], live: boolean): Record<AgentKey, SeatData> {
  const seats = Object.fromEntries(
    AGENTS.map((a) => [
      a.key,
      { state: "idle", saying: RESTING[a.key], toolCount: 0, tools: [] } as SeatData,
    ]),
  ) as Record<AgentKey, SeatData>;

  // events arrive newest-first from the API; replay oldest-first
  for (const e of [...events].reverse()) {
    switch (e.event) {
      case "agent_start": {
        const k = (e.agent ?? "boss") as AgentKey;
        seats[k].state = "working";
        seats[k].saying = `Reading ticket ${e.ticket_id}.`;
        break;
      }
      case "mcp_tool_call": {
        const k = (e.agent ?? "boss") as AgentKey;
        if (!seats[k]) break;
        seats[k].toolCount += 1;
        if (e.tool && !seats[k].tools.includes(e.tool)) seats[k].tools.push(e.tool);
        if (seats[k].state !== "done") seats[k].state = "working";
        seats[k].saying = e.tool
          ? `${TOOL_LABELS[e.tool] ?? e.tool}…`
          : seats[k].saying;
        break;
      }
      case "delegation_start": {
        const to = e.to as AgentKey;
        const from = e.frm as AgentKey;
        if (seats[to]) {
          seats[to].state = "working";
          seats[to].saying = e.question ? trim(e.question) : "On it.";
        }
        if (seats[from]) seats[from].saying = `Asked ${label(to)} to take a look.`;
        break;
      }
      case "delegation_end": {
        const to = e.to as AgentKey;
        if (seats[to]) {
          seats[to].state = "done";
          seats[to].saying = trim(e.recommendation || e.findings || "Reported back.");
        }
        break;
      }
      case "delegation_refused": {
        const from = e.frm as AgentKey;
        if (seats[from]) seats[from].saying = "Hit the delegation limit — answering with what I have.";
        break;
      }
      case "agent_end": {
        const k = (e.agent ?? "boss") as AgentKey;
        seats[k].state = "done";
        seats[k].saying = trim(e.decision || "Decided.");
        break;
      }
      case "run_end": {
        for (const a of AGENTS) if (seats[a.key].state === "working") seats[a.key].state = "done";
        break;
      }
    }
  }

  if (!live) {
    for (const a of AGENTS) if (seats[a.key].state === "working") seats[a.key].state = "done";
  }
  return seats;
}

/** One line per agent: which tools it touched on this ticket. */
export function summarise(seats: Record<AgentKey, SeatData>) {
  return AGENTS.filter((a) => seats[a.key].toolCount > 0 || seats[a.key].state === "done").map(
    (a) => ({
      key: a.key,
      role: a.role,
      line:
        seats[a.key].tools.length > 0
          ? seats[a.key].tools.map((t) => TOOL_LABELS[t] ?? t).join(", ")
          : "consulted, no tools needed",
      saying: seats[a.key].saying,
    }),
  );
}

export function latestRunId(events: TrailEvent[], ticketId: number | null): string | null {
  // No ticket picked means no run to show - the orchard rests rather than
  // replaying whatever happened last.
  if (!ticketId) return null;
  for (const e of events) {
    if (e.event === "run_start" && (e.open_tickets ?? []).includes(ticketId)) return e.run_id;
  }
  return null;
}

function label(key: AgentKey) {
  return AGENTS.find((a) => a.key === key)?.role ?? key;
}

function trim(text: string, max = 150) {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length <= max ? clean : `${clean.slice(0, max).trimEnd()}…`;
}
