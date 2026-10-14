# Campus Customs MCP Server

The shared toolbelt for the Campus Customs agent team. Every agent — Boss,
Inventory, Accounting, Facilities, Customer Service — reads the shop through
this server instead of touching SQLite directly, so there is one place where
the shop's rules and the "never invent data" discipline live.

## Database files

| File | Role |
|---|---|
| `../data/campus_customs_new.db` | **What this server reads and writes.** The working copy. |
| `../data/campus_customs.db` | The original. Never touched — copy it over the working file to reset a run. |

Shop "today" always comes from `desk.date_today` (2026-08-31), never the real
system clock, so overdue and due-soon math stays reproducible.

## Tools

Eleven tools. Ten are available to the agent team; `approve_and_pay` is not.

### Reading the shop

**`check_stock(sku, size="", qty_needed=0)`** — `inventory`. Units on hand
**by size** — inventory is keyed on (`sku`, `size`), so a SKU can look well
stocked while the requested size is empty. Pass `qty_needed` for `can_fill`
and `shortfall`.

**`list_open_tickets(ticket_id=0)`** — `tickets`, plus the `inventory`, `leases`
and `invoices` rows its pointers reach. The board. The only way to see a
ticket; pass an id to pull one regardless of status.

**`list_money_due()`** — `invoices`, `leases`, `cash_accounts`, `desk`,
`payments`. Everything owed now, dated against `desk.date_today` (negative
`days_until_due` = overdue), totalled against the balance.

**`check_vendor_can_ship(sku)`** — `vendors`, `invoices`, `inventory`, `desk`.
Who restocks a product, their `lead_days`, the earliest delivery from shop
today, and any unpaid invoice. `blocked: true` means no restock until it is
paid.

**`quote_discount(sku, qty, proposed_unit_price)`** — `pricing`. Unit cost,
list price, margin per unit and per order, discount off list, and `below_cost`.
Numbers only; whether to accept a discount is a judgment for the agents.

**`list_payment_requests(status="pending")`** — `payment_requests`. What is
waiting on a human, with the pending total against the cash balance. Call it
before raising a request so the same bill is not proposed twice.

### Changing the shop

**`request_payment(kind, ref_id, amount, reason, requested_by)`** —
`payment_requests`. Proposes a payment. **Moves no money.** The amount is
checked against what the database says is owed, so an invented figure is
refused, as is a duplicate pending request for the same bill.

**`resolve_ticket(ticket_id, resolution)`** — `tickets`. Closes a ticket with
the outcome appended to its notes. Refuses to re-close.

**`save_draft_message(ticket_id, message)`** — `tickets.notes`. Saves a
customer message as a draft on the board. **Nothing is sent** — there is no
send tool in this system.

**`update_inventory(sku, size, qty_delta, reason)`** — `inventory`. Adjusts
units on hand for a real physical movement. Refuses to go negative and refuses
a blank reason.

### Human only

**`approve_and_pay(request_id, approved_by)`** — `payments`, `cash_accounts`,
`invoices`, `leases`, `payment_requests`. The only tool that moves money, and
it is deliberately given to **no agent**. Refuses a blank approver and refuses
any payment that would overdraw the account. On success it writes a `payments`
row stamped with the approver, reduces the balance, and updates what was paid
(an invoice goes to `paid`, a lease rolls `next_due` forward a month).

### One added table

`payment_requests` is created in the working copy on first use. The provided
schema has nowhere to hold a proposed-but-unapproved payment, and writing
pending rows into `payments` would make a request look like money that moved.
`campus_customs.db` is never touched.

## Never inventing data

If a SKU, vendor, or specialty match is not in the database, these tools return
`found: false` / `matched: false` with a reason and a list of what *does* exist,
rather than guessing. `CC-HAT-BLUE` is the live example: no vendor specialty
clearly covers hats, so `check_vendor_can_ship` reports the ambiguity and lists
all vendors instead of picking one.

## Running it

The agent team starts this server itself over stdio, so it does not need to be running first. To drive it by hand:

```bash
pip install -r requirements.txt
python server.py          # stdio
python server.py --http   # http://127.0.0.1:8002/mcp
```

Set `CAMPUS_CUSTOMS_DB` to point the server at a throwaway copy of the database
for testing, so a test run never dirties the real working copy.

Port 8002 keeps 8000 free for the FastAPI backend.

## Connecting a vibe coder to it

`.mcp.json` in the repo root registers this server as `campus-customs`, using
paths relative to the repo root:

```json
{"mcpServers": {"campus-customs": {"command": ".venv/bin/python",
                                   "args": ["mcp_server/server.py"]}}}
```

Create the virtualenv at the repo root first (`python3 -m venv .venv &&
.venv/bin/pip install -r requirements.txt`) and the entry works from a fresh
clone without editing any paths. `output/mcp_smoke.json` is the evidence of
each tool being called this way.
