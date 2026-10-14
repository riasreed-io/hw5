import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { AGENTS, TOOL_LABELS } from "./agents";
import { AgentSeat } from "./components/AgentSeat";
import { Approvals } from "./components/Approvals";
import { TicketList } from "./components/TicketList";
import { deriveSeats, latestRunId, summarise } from "./derive";
import type { Board, Cash, PaymentRequest, RunResult, TrailEvent } from "./types";

const POLL_MS = 1200;

export default function App() {
  const [board, setBoard] = useState<Board | null>(null);
  const [cash, setCash] = useState<Cash | null>(null);
  const [requests, setRequests] = useState<PaymentRequest[]>([]);
  const [events, setEvents] = useState<TrailEvent[]>([]);
  const [health, setHealth] = useState<{ model: string; approver_on_record: string } | null>(null);
  const [selected, setSelected] = useState<number | null>(() => {
    // ?ticket=101 deep-links straight to a ticket, so a saved board or a
    // screenshot can point at one run.
    const q = new URLSearchParams(window.location.search).get("ticket");
    return q ? Number(q) : null;
  });
  const [running, setRunning] = useState<number | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);
  const [justResolved, setJustResolved] = useState<number | null>(null);
  const [cashFlash, setCashFlash] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const prevCash = useRef<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [b, c, p] = await Promise.all([api.tickets(), api.cash(), api.payments()]);
      setBoard(b);
      setRequests(p.requests);
      setCash((old) => {
        if (old && c.balance < old.balance) {
          setCashFlash(true);
          window.setTimeout(() => setCashFlash(false), 1600);
        }
        prevCash.current = c.balance;
        return c;
      });
      setError(null);
    } catch (e) {
      setError(
        `Can't reach the backend at ${import.meta.env.VITE_API_BASE ?? "http://localhost:8000"} — start it with: uvicorn main:app --reload --port 8000`,
      );
    }
  }, []);

  useEffect(() => {
    void refresh();
    api.health().then(setHealth).catch(() => undefined);
    api.events().then((d) => setEvents(d.events)).catch(() => undefined);
  }, [refresh]);

  // The desk is shared: tickets and cash can change from the CLI runner or a
  // second tab, so the board refreshes itself rather than waiting for a click.
  useEffect(() => {
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  // While a ticket runs, poll the audit trail so the apples move in step.
  useEffect(() => {
    if (running === null) return;
    const timer = window.setInterval(async () => {
      try {
        const d = await api.events();
        setEvents(d.events);
      } catch {
        /* the run is long; a dropped poll is not fatal */
      }
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [running]);

  const runId = useMemo(() => latestRunId(events, selected), [events, selected]);
  const runEvents = useMemo(
    () => (runId ? events.filter((e) => e.run_id === runId) : []),
    [events, runId],
  );
  const seats = useMemo(() => deriveSeats(runEvents, running !== null), [runEvents, running]);
  const summary = useMemo(() => summarise(seats), [seats]);

  // A finished run that happened before this page loaded still has everything
  // worth showing in the trail, so the board can reconstruct its summary.
  const pastResult = useMemo<RunResult | null>(() => {
    if (result || !selected) return null;
    const end = runEvents.find((e) => e.event === "agent_end" && e.agent === "boss");
    if (!end) return null;
    return {
      run_id: end.run_id,
      ticket_id: selected,
      decision: {
        ticket_id: selected,
        decision: end.decision ?? "",
        reasoning: end.reasoning ?? "",
        delegated_to: end.delegated_to ?? [],
        payment_requests: [],
        resolved: Boolean(end.resolved),
        awaiting_human: end.awaiting_human ?? "",
      },
      usage: { requests: 0, total_tokens: end.total_tokens ?? 0 },
    };
  }, [result, runEvents, selected]);

  const shown = result ?? pastResult;
  const selectedTicket = board?.tickets.find((t) => t.id === selected) ?? null;

  async function startRun(id: number) {
    setRunning(id);
    setResult(null);
    setError(null);
    try {
      const r = await api.runTicket(id);
      setResult(r);
      if (r.decision.resolved) {
        setJustResolved(id);
        window.setTimeout(() => setJustResolved(null), 2500);
      }
      const d = await api.events();
      setEvents(d.events);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(null);
      await refresh();
    }
  }

  async function approve(requestId: number) {
    try {
      await api.approve(requestId, health?.approver_on_record ?? "Rias Reed");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function resetAll() {
    await api.reset();
    setResult(null);
    setEvents([]);
    setSelected(null);
    await refresh();
  }

  return (
    <>
      <div className="field" aria-hidden>
        <div className="blob b1" /><div className="blob b2" />
        <div className="blob b3" /><div className="blob b4" />
      </div>

      <div className="shell">
        <header className="glass topbar">
          <div className="brand">
            <svg width="26" height="28" viewBox="0 0 100 108" aria-hidden>
              <path d="M50 22 C50 14 48 9 44 5" stroke="#6b4a2f" strokeWidth="4" strokeLinecap="round" fill="none" />
              <path d="M51 17 C60 7 74 6 79 9 C76 19 64 24 51 17 Z" fill="#2fa360" />
              <path d="M50 24 C40 14 20 18 13 34 C5 52 14 82 30 95 C38 101 44 97 50 97 C56 97 62 101 70 95 C86 82 95 52 87 34 C80 18 60 14 50 24 Z" fill="#111317" />
            </svg>
            <div>
              <h1>Campus Customs · Desk</h1>
              <p className="sub">
                {board ? `Shop day ${board.date_today}` : "Connecting…"}
                {health ? ` · ${health.model}` : ""}
              </p>
            </div>
          </div>

          <div className="spacer" />

          <span className="pill">
            <span className={`dot ${error ? "off" : ""}`} />
            {error ? "Backend offline" : "Backend live"}
          </span>
          <span className={`pill cashpill ${cashFlash ? "flash" : ""}`}>
            <small>Checking</small>
            ${cash ? cash.balance.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}
          </span>
          <button className="btn" onClick={resetAll} disabled={running !== null}>
            Reset shop
          </button>
        </header>

        {error && <div className="err">{error}</div>}

        <div className="grid">
          {/* ---------------- tickets ---------------- */}
          <div className="col">
            <section className="glass panel">
              <h2>The board</h2>
              <p className="hint">
                {board ? `${board.open} open · ${board.resolved} resolved` : "Loading tickets…"}
              </p>
              {board && (
                <TicketList
                  tickets={board.tickets}
                  selected={selected}
                  runningId={running}
                  justResolved={justResolved}
                  onSelect={(id) => {
                    setSelected(id);
                    setResult(null);
                    const url = new URL(window.location.href);
                    url.searchParams.set("ticket", String(id));
                    window.history.replaceState({}, "", url);
                  }}
                />
              )}
            </section>
          </div>

          {/* ---------------- stage ---------------- */}
          <div className="col">
            <section className="glass stage">
              <div className="stage-head">
                <h2>{selectedTicket ? selectedTicket.subject : "Pick a ticket"}</h2>
                <span className="where">
                  {selectedTicket ? `#${selectedTicket.id} · ${selectedTicket.requester}` : "the orchard is resting"}
                </span>
                <div className="spacer" style={{ flex: 1 }} />
                <button
                  className="btn primary"
                  disabled={!selected || running !== null}
                  onClick={() => selected && startRun(selected)}
                >
                  {running !== null ? "Team working…" : "Start the team"}
                </button>
              </div>
              <p className="stage-sub">
                {selectedTicket
                  ? selectedTicket.notes?.split("\n")[0]
                  : "Five agents, five apples. Choose a ticket on the left and watch who the Boss actually calls — nobody wakes up unless they are needed."}
              </p>

              <div className="orchard">
                {AGENTS.map((skin) => (
                  <AgentSeat key={skin.key} skin={skin} data={seats[skin.key]} />
                ))}
              </div>

              {shown && (
                <div className="summary">
                  <h3>
                    What the desk decided
                    {shown.decision.resolved && <span className="chip resolved" style={{ marginLeft: 8 }}>Resolved</span>}
                  </h3>
                  <p>{shown.decision.decision}</p>
                  {shown.decision.awaiting_human && (
                    <div className="await">Waiting on you: {shown.decision.awaiting_human}</div>
                  )}
                  {summary.map((s) => (
                    <div className="sumrow" key={s.key}>
                      <span className="who">{s.role}</span>
                      <span className="what">{s.line}</span>
                    </div>
                  ))}
                  <div className="sumrow">
                    <span className="who">Run cost</span>
                    <span className="what">
                      {shown.usage.total_tokens.toLocaleString()} tokens
                      {shown.usage.requests > 0 ? ` over ${shown.usage.requests} model requests` : ""}
                    </span>
                  </div>
                </div>
              )}
            </section>
          </div>

          {/* ---------------- right rail ---------------- */}
          <div className="col col-right">
            <section className="glass panel">
              <h2>Checking</h2>
              <div className="ledger">
                <div className="big">
                  ${cash ? cash.balance.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}
                </div>
                <div className="lrow">
                  <span>Pending approvals</span>
                  <b>${cash ? cash.pending_total.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "—"}</b>
                </div>
                <div className="lrow">
                  <span>If you approve everything</span>
                  <b>
                    ${cash
                      ? cash.cash_if_all_pending_approved.toLocaleString(undefined, { minimumFractionDigits: 2 })
                      : "—"}
                  </b>
                </div>
              </div>
            </section>

            <section className="glass panel">
              <h2>Needs a human</h2>
              <p className="hint">Agents prepare. You release.</p>
              <Approvals
                requests={requests}
                approver={health?.approver_on_record ?? "Rias Reed"}
                onApprove={approve}
              />
            </section>

            <section className="glass panel">
              <h2>Live trail</h2>
              <p className="hint">{runEvents.length} events this run</p>
              <div className="feed">
                {runEvents.length === 0 && <p className="empty">Nothing yet. Start a ticket.</p>}
                {runEvents.slice(0, 40).map((e, i) => (
                  <div className="ev" key={`${e.ts}-${i}`}>
                    <span className={`tag ${tagClass(e.event)}`}>{tagText(e.event)}</span>
                    <span className="txt">{eventText(e)}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    </>
  );
}

function tagClass(event: string) {
  if (event === "mcp_tool_call") return "tool";
  if (event.startsWith("delegation")) return event === "delegation_refused" ? "stop" : "deleg";
  if (event === "human_approval") return "money";
  return "";
}

function tagText(event: string) {
  const map: Record<string, string> = {
    mcp_tool_call: "tool",
    delegation_start: "asks",
    delegation_end: "replies",
    delegation_refused: "limit",
    agent_start: "start",
    agent_end: "decides",
    run_start: "run",
    run_end: "done",
    human_approval: "paid",
  };
  return map[event] ?? event;
}

function eventText(e: TrailEvent) {
  switch (e.event) {
    case "mcp_tool_call":
      return `${role(e.agent)} — ${TOOL_LABELS[e.tool ?? ""] ?? e.tool}`;
    case "delegation_start":
      return `${role(e.frm)} → ${role(e.to)}`;
    case "delegation_end":
      return `${role(e.to)} → ${role(e.frm)}: ${(e.recommendation || e.findings || "").slice(0, 90)}`;
    case "delegation_refused":
      return `${role(e.frm)} stopped at the depth limit`;
    case "agent_end":
      return `${role(e.agent)} decided · ${e.total_tokens?.toLocaleString() ?? "?"} tokens`;
    case "human_approval":
      return `Payment request ${e.request_id ?? ""} released by ${e.actor ?? "a human"}`;
    case "run_start":
      return `Run started on ticket ${(e.open_tickets ?? []).join(", ")}`;
    case "run_end":
      return "Run finished";
    default:
      return e.event;
  }
}

function role(key?: string) {
  return AGENTS.find((a) => a.key === key)?.role ?? key ?? "—";
}
