# Campus Customs — Agent Harness Notes

Working notes for the multi-agent shop operations build. This file grows with
each problem.

- Original (never written to): `data/campus_customs.db`
- Working copy (MCP server + backend point here): `data/campus_customs_new.db`
- Shop "today" = `desk.date_today` = **2026-08-31**

---

## 1. Tables, fields, and why each one matters to the agents

### `desk` — 1 row
| Field | Type | Example |
|---|---|---|
| `date_today` | TEXT | `2026-08-31` |
| `notes` | TEXT | (empty) |

**Why it matters:** this is the shop's clock. Every "is it overdue / is it due
soon" judgment any agent makes has to be measured against `date_today`, not the
real wall clock.

### `tickets` — 3 rows (all `open`)
| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | 101, 102, 103 |
| `type` | TEXT | `customer_order`, `rent_notice`, `price_override` |
| `requester` | TEXT | customer, landlord, or student org |
| `subject` | TEXT | short title |
| `sku` | TEXT | nullable — links to `inventory` / `pricing` |
| `size` | TEXT | nullable — with `sku`, the `inventory` primary key |
| `qty` | INTEGER | nullable — how many units requested |
| `lease_id` | INTEGER FK → `leases.id` | nullable |
| `invoice_id` | INTEGER FK → `invoices.id` | nullable |
| `status` | TEXT | `open` for all three right now |
| `notes` | TEXT | the human-readable ask |
| `created_at` | TEXT | ISO timestamp |

**Why it matters:** this is the board. The Boss agent reads `type` to decide who
to route to, and the nullable FK columns (`sku`/`size`, `lease_id`,
`invoice_id`) are the pointers that tell the specialist agent which other table
to go open.

### `inventory` — 10 rows, PK (`sku`, `size`)
| Field | Type | Notes |
|---|---|---|
| `sku` | TEXT | 4 SKUs |
| `name` | TEXT | display name |
| `size` | TEXT | `S/M/L/XL`, or `OS` for one-size |
| `qty` | INTEGER | units on hand |
| `location` | TEXT | Aisle A–D |

**Why it matters:** the Inventory agent's source of truth for "can we fill this
today?" Stock is per **size**, not per SKU — a SKU with plenty of total units
can still be zero in the size that was asked for.

### `pricing` — 4 rows
| Field | Type | Notes |
|---|---|---|
| `sku` | TEXT PK | one row per SKU, not per size |
| `unit_cost` | REAL | what we pay |
| `list_price` | REAL | what we charge |

**Why it matters:** the Accounting agent's margin check. Any discount on ticket
103 has to be evaluated as `discounted_price - unit_cost`, and this is the only
table that knows cost.

### `vendors` — 3 rows
| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | 1–3 |
| `name` | TEXT | Bulldog Print Co, Elm City Gifts, QuickShip CT |
| `specialty` | TEXT | apparel reprint / mugs and small goods / local courier |
| `lead_days` | INTEGER | 5 / 3 / 1 |

**Why it matters:** restock routing. Inventory picks a vendor by `specialty` and
promises a date using `lead_days` — and the "no shipping while an invoice is
unpaid" rule attaches to the **vendor**, so this is also where a restock plan
gets blocked.

### `leases` — 1 row
| Field | Type | Value |
|---|---|---|
| `id` | INTEGER PK | 1 |
| `space_name` | TEXT | Chapel Street shop |
| `landlord` | TEXT | Elm City Properties |
| `monthly_rent` | REAL | 2400.0 |
| `next_due` | TEXT | 2026-09-02 |
| `notes` | TEXT | (empty) |

**Why it matters:** the Facilities agent's table. `next_due` vs `date_today` is
how rent urgency is computed, and `monthly_rent` is a large claim on the same
cash pool the vendor invoice wants.

### `cash_accounts` — 1 row
| Field | Type | Value |
|---|---|---|
| `name` | TEXT PK | checking |
| `balance` | REAL | 3400.0 |
| `date` | TEXT | 2026-08-31 |

**Why it matters:** the hard constraint. One account, 3400.0, and money only
goes out in this homework. The pay tool must refuse rather than let this go
negative.

### `payments` — 0 rows (agents fill this in)
| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `kind` | TEXT | e.g. invoice vs rent |
| `ref_id` | INTEGER | the `invoices.id` or `leases.id` being paid |
| `amount` | REAL | |
| `account` | TEXT | → `cash_accounts.name` |
| `paid_at` | TEXT | |
| `approved_by` | TEXT | **the human-approval audit trail** |

**Why it matters:** the write-side proof of work. Empty today; every approved
payment the agents make gets logged here, and `approved_by` is what shows a
human signed off before cash moved.

### `invoices` — 1 row
| Field | Type | Value |
|---|---|---|
| `id` | INTEGER PK | 501 |
| `vendor_id` | INTEGER FK → `vendors.id` | 1 (Bulldog Print Co) |
| `amount` | REAL | 840.0 |
| `due_date` | TEXT | 2026-08-28 |
| `status` | TEXT | open |
| `description` | TEXT | Rush reprint CC-TEE-WHITE S |

**Why it matters:** the chokepoint. One open, **already-overdue** invoice that
blocks the only apparel vendor from shipping anything new.

---

## 2. The three open tickets and how they link

### Ticket 101 — `customer_order`, Tauhid Zaman, "Bulldog tee"
Wants `CC-TEE-WHITE` size **S**, qty 1. Carries `invoice_id = 501`.

- `inventory(CC-TEE-WHITE, S).qty = 0` → **cannot fill from stock** (M=5, L=3,
  XL=2 exist, but not S)
- restock → `vendors.specialty = 'apparel reprint'` → vendor 1, `lead_days = 5`
- vendor 1 has invoice 501 open (840.0, due 2026-08-28, **3 days overdue**)
- → vendor won't ship until 501 is paid → paying 501 needs human approval
- `pricing(CC-TEE-WHITE)`: cost 8.0, list 28.0

**Chain:** tickets → inventory (short) → vendors (who reprints) → invoices
(blocked) → cash_accounts (can we pay?) → payments (log it).

### Ticket 102 — `rent_notice`, Elm City Properties, "Rent due"
Carries `lease_id = 1`.

- `leases(1)`: 2400.0 due 2026-09-02 → **2 days out** from `date_today`
- paid from `cash_accounts.checking` = 3400.0
- also needs human approval, also logs to `payments`

**Chain:** tickets → leases → cash_accounts → payments.

### Ticket 103 — `price_override`, Yale AI Club, "Bulk hoodie discount"
Wants `CC-HOOD-NAVY` size **M**, qty **20**, asking for a bulk discount.

- `inventory(CC-HOOD-NAVY, M).qty = 8` → **12 short** (S=4, L=14, XL=6 are the
  wrong size)
- `pricing(CC-HOOD-NAVY)`: cost 22.0, list 58.0 → 20 @ list = 1160.0, margin
  headroom 36.0/unit before cost
- restock of the 12 → apparel again → vendor 1 → blocked by invoice 501 as well

**Chain:** tickets → inventory (short) → pricing (margin floor) → vendors →
invoices → human approval on the discount.

---

## 3. The cash squeeze (why ordering matters)

Checking has **3400.0**, and both payable items are live at once:

| Claim | Amount | Timing |
|---|---|---|
| Invoice 501 (vendor 1) | 840.0 | overdue since 2026-08-28 |
| Rent, lease 1 | 2400.0 | due 2026-09-02 |
| **Total** | **3240.0** | leaves **160.0** |

Both fit — but only if nothing else goes out first, and only if the agents don't
double-pay. Paying rent alone leaves 1000.0, which still covers 840.0; the
reverse also works. A third payment of any size breaks it, and the pay tool must
refuse rather than go negative.

---

## 4. Open decisions (settled in Problem 5)

All four are now shop policy in `backend/models.py` (`ShopPolicy`) and are
injected into every agent prompt:

1. **Discount floor** — never below unit cost; anything under a 25% gross
   margin needs the Boss to sign off explicitly. The hard floor (unit cost) is
   the only line the data itself draws — below it every unit loses money. The
   25% is a judgment call, set so the hoodie's 22.00 cost supports a floor
   price near 29.00, well under the 58.00 list, leaving real room to discount
   in bulk without the shop working for nothing.
2. **Partial fulfilment** — allowed: ship what is on hand now and the rest on
   restock, as long as the customer is told both dates.
3. **Payment ordering** — rent before vendor bills on principle; when cash
   covers both, they go in the same approval batch so no vendor stays blocked.
4. **The human** — `payments.approved_by` is "Rias Reed".

---

## 5. MCP tools (Problem 3)

Server: `mcp_server/server.py` (FastMCP), pointed at
`data/campus_customs_new.db`. All three are read-only for now; the payment
tool arrives with the human-approval flow.

### `check_stock(sku, size="", qty_needed=0)`
- **Tables read:** `inventory`
- **Unlocks:** tickets **101** and **103**
- **Verified output:** 101 → `CC-TEE-WHITE/S` = 0 on hand, shortfall 1 (M=5,
  L=3, XL=2 exist). 103 → `CC-HOOD-NAVY/M` = 8 of 20, shortfall 12.
- **Why it's the right tool:** i like the size vs sku angle here — it makes sure these are separate
  completely and not mixed up at all (101 = S tee, 0 on hand; 103 = 20 in M,
  8 on hand).

### `list_money_due()`
- **Tables read:** `invoices`, `leases`, `cash_accounts`, `desk`, `payments`
- **Unlocks:** ticket **102**
- **Verified output:** rent 2400.00 due 2026-09-02 (2 days out) and invoice 501
  for 840.00 overdue by 3 days, against 3400.00 cash → 160.00 left if both are
  paid.
- **Why it's the right tool:** rent against the other claims — so it can't be claimed elsewhere, which is
  helpful so that things don't get mixed up and go negative (2400 rent due in
  2 days, 840 already overdue, 3400 in checking).

### `check_vendor_can_ship(sku)`
- **Tables read:** `vendors`, `invoices`, `inventory`, `desk`
- **Unlocks:** ticket **101** (and the restock half of **103**)
- **Verified output:** `CC-TEE-WHITE` → Bulldog Print Co, 5-day lead,
  `blocked: true` on invoice 501, 840.00 to unblock, earliest delivery
  2026-09-05 once paid.
- **Why it's the right tool:** this one names the actual blocker so we can identify what the actual problem
  is and get to the bottom of resolving it sooner than later, which is helpful
  for efficiency (invoice 501 freezes the only apparel vendor, 840 to unblock).
---

## 6. MCP connection + smoke test (Problem 4)

- Connection JSON: `.mcp.json` in this folder (server name `campus-customs`),
  with the same entry added to the monorepo root `.mcp.json` so the vibe coder
  running from the parent folder can reach it.
- Interpreter: `.venv/bin/python` in this folder, `fastmcp` 4.1.0.
- Evidence: `output/mcp_smoke.json` — one entry per tool with the prompt, the
  tool name, the arguments, and the verbatim tool output, each cross-checked
  against a direct SQL read of `data/campus_customs_new.db`.
- Working copy is still byte-identical to the original after testing (same
  md5), because all three tools are read-only.

**Two things the smoke test exposed, for later problems:**

1. **No ticket lookup.** A prompt that only says "ticket 101" gives the agents
   nothing — none of the three tools can read the `tickets` table, so the SKU
   and size have to be handed in from the board. The Boss agent will need
   either a `get_ticket` tool or the ticket row passed in its prompt.
2. **SKU guessing is correctly refused.** Asked about "the white tee", the vibe
   coder tried `sku="white tee"` and `sku="TEE-WHT"`; both came back
   `matched: false` with the real vendor list attached instead of a invented
   match.

---

## 7. The agent team (Problem 5)

Five agents, all on `gpt-6-luna` through Portkey, all reading the shop only
through the MCP server. Prompts live one per file in `backend/prompts/`.

| Agent | Owns | MCP tools it holds |
|---|---|---|
| **Boss** | Reads every ticket, routes, decides, closes. The only agent the human talks to; the human can override it. | `list_open_tickets`, `resolve_ticket` |
| **Inventory** | Stock by size, shortfalls, restock paths, lead times, physical stock changes. | `list_open_tickets`, `check_stock`, `check_vendor_can_ship`, `update_inventory` |
| **Accounting** | Cash, invoices, margins, discounts, payment requests. Does what the Boss asks without breaking accounting principles. | `list_open_tickets`, `list_money_due`, `quote_discount`, `check_vendor_can_ship`, `request_payment`, `list_payment_requests` |
| **Facilities** | The lease, the landlord, rent and its dates. Rent before vendor bills on principle; carries a ticket to the point of closing. | `list_open_tickets`, `list_money_due`, `request_payment`, `list_payment_requests` |
| **Customer Service** | Everything a customer reads. Warm, and promises nothing without the Boss. | `list_open_tickets`, `check_stock`, `save_draft_message` |

**Full connectivity:** every agent carries an `ask_<colleague>` tool for each of
the other four, so any agent can delegate to any other. Delegation depth is
capped at 2.

### Every MCP tool and the tables behind it

| Tool | Tables | R/W | Used by |
|---|---|---|---|
| `check_stock` | `inventory` | read | Inventory, Customer Service |
| `list_money_due` | `invoices`, `leases`, `cash_accounts`, `desk`, `payments` | read | Accounting, Facilities |
| `check_vendor_can_ship` | `vendors`, `invoices`, `inventory`, `desk` | read | Inventory, Accounting |
| `list_open_tickets` | `tickets` (+ `inventory`, `leases`, `invoices`) | read | all five |
| `quote_discount` | `pricing` | read | Accounting |
| `list_payment_requests` | `payment_requests`, `invoices`, `leases`, `cash_accounts` | read | Accounting, Facilities |
| `request_payment` | `payment_requests` (checks `invoices`, `leases`, `cash_accounts`) | write | Accounting, Facilities |
| `resolve_ticket` | `tickets` | write | Boss only |
| `save_draft_message` | `tickets.notes` | write | Customer Service |
| `update_inventory` | `inventory` | write | Inventory |
| `approve_and_pay` | `payments`, `cash_accounts`, `invoices`, `leases`, `payment_requests` | write | **no agent — human only** |

`payment_requests` is one table added to the working copy. The provided schema
has nowhere to hold a payment that has been proposed but not approved, and
writing pending rows into `payments` would make an unapproved request look like
money that moved. `campus_customs.db` is untouched, so a reset still restores
the shop exactly as handed out.

---

## 8. Safety and limits

### The three that matter most — in my words

> **The approved-by field is good because it can then trace that it was claimed
> by a person. It should never be approved by AI.**

> **No agent holds approve-and-pay, so that it isn't possible for them to
> approve.**

> **I like that request_payment checks the amount owed, so it can't make up
> figures.**

Those three are the spine of this system: a payment can only exist for a real
debt, no agent can release it, and whoever did release it is named on the row.
The rest below are the supporting checks.

### The full list of guardrails

**Money cannot move without a human.** No agent holds `approve_and_pay`. The
most the entire team can do is write a pending row. This is structural, not a
prompt instruction — an agent that decided to pay itself has no tool to do it
with.

**The approver is named and recorded.** `payments.approved_by` is required and
non-blank, so every cent that leaves the account traces to a person.

**No overdrafts, ever.** `approve_and_pay` refuses if the balance would go
negative, and the refusal is a tool-level check, not a judgment call.

**You can only request what you owe.** `request_payment` compares the amount to
the database and refuses a mismatch, so a hallucinated figure cannot become a
request. Duplicate pending requests for the same bill are refused too.

**Nothing reaches a customer.** There is no send tool anywhere in the system.
Customer Service drafts onto the ticket; a human decides whether to send it.

**No invented facts.** Every tool returns `found: false` with the real options
when something is missing, rather than guessing — the vendor tool refuses to
match a SKU it cannot place, and every prompt ties claims to tool results.

**Stock cannot go impossible.** `update_inventory` refuses negatives and
requires a written reason, so no stock change is unexplainable afterwards.

**Everything is auditable.** Every tool call, delegation, decision and approval
appends to `output/audit_trail.json` with timestamps and token counts. The file
is append-only, so a later run cannot quietly rewrite an earlier one.

**One source of truth.** No agent has shop tools outside MCP, so there is no
second code path that could bypass these checks.

### Limits that keep token use in check

| Limit | Value | Why |
|---|---|---|
| Delegation depth | 2 | Boss → specialist → one more. Stops A-asks-B-asks-C-asks-A loops; refusals are logged. |
| Model requests per ticket | 60 | Shared across the whole delegation chain, not per agent. |
| Tool calls per ticket | 90 | MCP plus delegation calls combined. |
| Tokens per ticket | 200,000 | Hard ceiling; the run aborts rather than spends past it. |
| Tool visibility | per agent | Each agent sees only its own tools, so nine schemas are not loaded into five agents' every request. |
| Audit previews | 400 chars | Arguments and results are truncated in the log instead of stored whole. |

Measured on the live run: 161,803 tokens total for three tickets — 49,030 for
ticket 101, 25,206 for 102, 87,567 for 103. Ticket 103 alone shows why the
ceilings matter: it used 28 model requests against the 60 cap.

---

## 9. Backend routes (Problem 7)

`backend/main.py`, FastAPI. Started from the `backend/` folder with
`uvicorn main:app --reload --port 8000`, so the dashboard calls
`http://localhost:8000`. The app has no database access of its own — every
fact and every write goes through the MCP server.

| Route | What it does |
|---|---|
| `GET /api/health` | Backend is up, which model a run would use, the approver on record, and the token limits. |
| `GET /api/tickets` | All three tickets with whether each is open or resolved, plus the rows their pointers reach. |
| `GET /api/tickets/{id}` | One ticket with its inventory, lease or invoice context. 404 if it does not exist. |
| `POST /api/tickets/{id}/run` | Runs the agent team on that ticket and returns the Boss's decision and token usage. Cannot move money. |
| `GET /api/events?limit=&run_id=` | Recent agent events, newest first — what each agent said, which tools they called, which delegations happened. The board polls this. |
| `GET /api/payments?status=pending` | Payment requests waiting on a human, with the cash they would consume. |
| `POST /api/payments/{id}/approve` | The human click. **The only route that changes cash.** Refuses overdrafts and already-decided requests, records the approver. |
| `GET /api/cash` | The current checking balance from `cash_accounts`, with pending requests against it. |
| `POST /api/reset` | Restores the working database from the original for a fresh run. |

**The split that matters:** `/run` lets the agents prepare and raise payment
requests; `/approve` is the only path that moves money, and no agent can reach
it. One run at a time is enforced by a lock, so two runs cannot interleave
their writes.

---

## 10. The dashboard (Problem 8)

`frontend/`, React + Vite + TypeScript, started with `npm run dev`. It calls
the Problem 7 routes at `http://localhost:8000` (override with
`VITE_API_BASE`). The backend allows any `localhost` origin, so the vite port
does not have to be 5173 — this machine already had 5173 taken, so the desk
runs on **5181**.

| Region | What it shows |
|---|---|
| Top bar | Shop day, model, backend status, checking balance, reset |
| The board (left) | All three tickets with Open / Running / Resolved chips |
| The stage (centre) | Five apples — one per agent — animating while they work, each with a speech bubble of what it is doing in plain English |
| Decision panel | The Boss's outcome, what is still waiting on a human, one line per agent of which tools it used, and the token cost |
| Checking (right) | Balance, pending approvals, and what the balance becomes if everything pending is approved |
| Needs a human (right) | Pending payment requests with an Approve & pay button — the only control in the UI that moves money |
| Live trail (right) | The audit trail streaming as colour-coded events |

Each agent is a different apple variety — Boss a Red Delicious, Inventory a
Granny Smith, Accounting a Golden Delicious, Facilities a Fuji, Customer
Service a Honeycrisp — so who was involved reads at a glance. Agents that were
never called stay desaturated and asleep for the whole run, which is how the
board shows that the Boss did *not* wake everyone. Full design reasoning is in
`output/design.md`.

`?ticket=101` deep-links to a ticket, and a finished run's summary is
reconstructed from the audit trail, so a reloaded page still shows what
happened.

---

## 11. The resolved run (2026-10-14)

Database reset first, then all three tickets run through the API with a human
approval after each.

| Ticket | Boss called first | Delegated to | Passes | Tokens | Cash |
|---|---|---|---|---|---|
| 101 Bulldog tee | Inventory | Inventory, Accounting, Customer Service | 3 | 159,525 | −840.00 |
| 102 Rent due | Accounting | Accounting only | 1 | 20,550 | −2,400.00 |
| 103 Bulk hoodie | Accounting | Accounting, Inventory, Customer Service | 1 | 69,725 | 0.00 |

**Cash:** 3,400.00 → 2,560.00 (invoice 501) → 160.00 (rent) → 160.00. Verified
against `cash_accounts` after the run.

**Facilities was never called on any ticket**, including the rent ticket it
owns — the Boss treated rent as a cash question for Accounting. That is the
single biggest gap between the plan in `desk_tickets.html` and what happened.

Ticket 101 needed three passes. The first two left it open because the Boss
prompt forbade closing a ticket whose work was not done, and the reprint does
not arrive until 2026-09-05. The prompt was amended between passes 2 and 3 to
allow closing when the only remaining step is outside the shop's hands, with
the outstanding item named in the resolution.

Artifacts from this run: `output/resolved_tickets.json`,
`output/resolved_board.html` (with `output/screenshots/`), the Actual and Cash
tabs of `output/desk_tickets.html`, and every step appended to
`output/audit_trail.json`.
