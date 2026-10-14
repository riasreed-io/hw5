# Campus Customs — Multi-Agent Operations

MGT 409 Homework 5. A five-agent team runs the back office of Campus Customs, a
Yale apparel shop on Chapel Street: it reads the ticket board, checks stock,
prices discounts, prepares payments, drafts customer replies, and closes
tickets — while a human keeps the only key to the cash.

Three pieces talk to each other:

- **`mcp_server/`** — a FastMCP server with 11 tools over the shop's SQLite
  database. Every shop fact the agents know comes through here.
- **`backend/`** — five pydantic-ai agents (Boss, Inventory, Accounting,
  Facilities, Customer Service) on `gpt-6-luna` through Portkey, plus a FastAPI
  app the dashboard calls.
- **`frontend/`** — a React + Vite + TypeScript board where you pick a ticket,
  watch the agents work, and approve payments.

**The rule the whole thing is built around:** agents prepare, humans release.
No agent holds `approve_and_pay`, so no agent can move money. The most the team
can do is raise a payment request with the exact amount the database says is
owed.

---

## The three tickets

| # | Ticket | The catch |
|---|---|---|
| 101 | Tauhid Zaman wants 1 white tee, size S | 0 in stock; the only apparel vendor is blocked by an overdue invoice |
| 102 | Rent notice from Elm City Properties | 2,400.00 due in two days, competing for the same cash |
| 103 | Yale AI Club wants 20 navy hoodies in M | Only 8 in M, and they want a bulk discount |

Shop "today" is **2026-08-31**, read from `desk.date_today` — never the real
clock.

---

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env     # then put your PORTKEY_API_KEY in it
```

Every agent uses **`gpt-6-luna` through Portkey**, and `backend/agents.py`
raises rather than start with any other model. Every run also records the model
it used: each `run_start` line in `output/audit_trail.json` carries
`"model": "gpt-6-luna (via Portkey)"`, across all 14 runs in the trail.

---

## Copy the original database to the working copy

`data/campus_customs.db` is the shop exactly as it was handed out, and nothing
ever writes to it. `data/campus_customs_new.db` is the working copy that the
MCP server and the backend read and write.

When you want a clean run:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

Both files are committed, so a fresh clone can run immediately. There is also a
`POST /api/reset` route and a **Reset shop** button on the dashboard that do
exactly this copy.

---

## Start the MCP server

The agents and the backend launch it themselves over stdio, so you usually do
not need to start it by hand. To drive it directly:

```bash
cd mcp_server
../.venv/bin/python server.py          # stdio
../.venv/bin/python server.py --http   # http://127.0.0.1:8002/mcp
```

`.mcp.json` registers it for a vibe coder as `campus-customs`. Set
`CAMPUS_CUSTOMS_DB` to point it at a throwaway copy when testing.

---

## Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

That serves <http://localhost:8000> — the routes the dashboard calls. Interactive
docs at <http://localhost:8000/docs>.

| Route | What it does |
|---|---|
| `GET /api/tickets` | All three tickets and whether each is open or resolved |
| `POST /api/tickets/{id}/run` | Runs the agent team on one ticket. Cannot move money |
| `GET /api/events` | Recent agent events — what each agent said and which tools it used |
| `GET /api/payments` | Payment requests waiting on a human |
| `POST /api/payments/{id}/approve` | **The only route that changes cash** |
| `GET /api/cash` | The checking balance from `cash_accounts` |
| `POST /api/reset` | Restores the working database from the original |

---

## Start the React board

```bash
cd frontend
npm install
npm run dev
```

The board talks to `http://localhost:8000`. If your backend is on a different
port, put `VITE_API_BASE=http://localhost:8001` in `frontend/.env.local`.

Pick a ticket, press **Start the team**, and watch: each agent is an apple that
wakes up only when it is called, with a speech bubble of what it is doing.
Approve payments in the right-hand rail and the balance drops.

---

## Reset before a full three-ticket run

Always start a full run from the original data, or the numbers will not line up:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

Then either run all three tickets from the terminal:

```bash
.venv/bin/python backend/run_tickets.py --reset --approve
```

(`--reset` does the copy for you; `--approve` releases the pending payments as
the shop owner afterwards.)

Or use the board: **Reset shop**, then run 101, 102 and 103 in turn, approving
payments as they appear.

A full three-ticket run costs roughly 150k–250k tokens, so reset deliberately
rather than often.

---

## What a correct run looks like

| | |
|---|---|
| Starting checking balance | 3,400.00 |
| Invoice 501 to Bulldog Print Co (ticket 101) | −840.00 |
| Rent to Elm City Properties (ticket 102) | −2,400.00 |
| Ticket 103 | no money moves |
| **Ending balance** | **160.00** |

Both payments land in `payments` stamped `approved_by = "Rias Reed"`, invoice
501 flips to `paid`, and the lease's `next_due` rolls to 2026-10-02.

---

## Where to look

| Path | What it is |
|---|---|
| `AI_prompts.md` | Every prompt I typed into the vibe coder, per problem |
| `output/harness.md` | The full build notes: tables, all 11 MCP tools, the five agents, the API routes, the dashboard, and the safety rules |
| `output/desk_tickets.html` | Double-click. What I expected per ticket, what actually happened, the cash reconciliation, and my reflection |
| `output/resolved_board.html` | Double-click. The live dashboard captured for each resolved ticket |
| `output/resolved_tickets.json` | Per ticket: final status, outcome, what each agent contributed, human approvals |
| `output/design.md` | Why the dashboard looks the way it does |
| `output/mcp_smoke.json` | Evidence of each MCP tool being called by the vibe coder |
| `output/audit_trail.json` | Append-only: every tool call, delegation, decision and approval, across every run |
| `backend/prompts/` | The five agent prompts, one file each |
| `output/screenshots/` | The board captured for each resolved ticket |

---

## Verifying a run yourself

After a run, check the shop's own books rather than taking the board's word:

```bash
sqlite3 data/campus_customs_new.db \
  "select id, status from tickets;
   select name, balance from cash_accounts;
   select id, kind, amount, approved_by from payments;
   select id, status from invoices;"
```

A correct full run leaves all three tickets `resolved`, checking at `160.0`,
two rows in `payments` both approved by a named human, and invoice 501 `paid`.
No row in `payments` should ever have a blank `approved_by` — the pay tool
refuses it.
