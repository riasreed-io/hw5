"""Campus Customs MCP — the shared toolbelt for the agent team.

Every agent (Boss, Inventory, Accounting, Facilities, Customer Service) reads
the shop through this server. Three tools for now; more get added in later
problems.

Reads the WORKING COPY, data/campus_customs_new.db. The original,
data/campus_customs.db, is never touched so a run can be reset.

Rule these tools follow: never invent data. If a SKU, vendor, or row is not in
the database, the tool says so and reports what IS there, rather than guessing.

Run from this folder (stdio):  python server.py
Run (HTTP):                    python server.py --http
HTTP URL:                      http://127.0.0.1:8002/mcp
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# The working copy. CAMPUS_CUSTOMS_DB can point this at a throwaway copy for
# tests, so a test run never dirties the real working database.
DB_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_DB") or ROOT / "data" / "campus_customs_new.db")

mcp = FastMCP("campus-customs")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _today(conn: sqlite3.Connection) -> str:
    """Shop 'today' comes from desk.date_today, never the real clock."""
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    return row["date_today"]


def _days_until(today: str, when: str) -> int:
    """Negative means overdue by that many days."""
    return (date.fromisoformat(when) - date.fromisoformat(today)).days


# Maps a SKU's product word to a word that appears in vendors.specialty.
# Deliberately incomplete: CC-HAT-BLUE has no entry because no vendor
# specialty in the database clearly covers hats, and guessing one would be
# inventing data. Unmapped SKUs come back with every vendor listed instead.
SKU_WORD_TO_SPECIALTY = {
    "TEE": "apparel",
    "HOOD": "apparel",
    "MUG": "mugs",
}


@mcp.tool
def check_stock(sku: str, size: str = "", qty_needed: int = 0) -> dict:
    """Check units on hand for a product, by size.

    Inventory is keyed on (sku, size), so a SKU with plenty of stock overall
    can still be empty in the size a customer asked for. Pass `size` to check
    one size, or leave it blank to see every size for the SKU. Pass
    `qty_needed` to also get the shortfall for an order of that many units.

    Returns the matching rows with qty and location, plus `can_fill` and
    `shortfall` when both `size` and `qty_needed` are given.
    """
    with _conn() as conn:
        if size:
            rows = conn.execute(
                "SELECT sku, name, size, qty, location FROM inventory "
                "WHERE sku = ? AND size = ?",
                (sku, size),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT sku, name, size, qty, location FROM inventory "
                "WHERE sku = ? ORDER BY size",
                (sku,),
            ).fetchall()

        if not rows:
            # Say what exists rather than guessing at what was meant.
            known = conn.execute(
                "SELECT DISTINCT sku FROM inventory ORDER BY sku"
            ).fetchall()
            sizes = conn.execute(
                "SELECT size FROM inventory WHERE sku = ? ORDER BY size",
                (sku,),
            ).fetchall()
            return {
                "found": False,
                "sku": sku,
                "size": size,
                "reason": (
                    f"No inventory row for sku={sku!r} size={size!r}."
                    if sizes
                    else f"No inventory rows for sku={sku!r}."
                ),
                "sizes_carried_for_this_sku": [r["size"] for r in sizes],
                "known_skus": [r["sku"] for r in known],
            }

        result = {
            "found": True,
            "sku": sku,
            "rows": [dict(r) for r in rows],
            "other_sizes": [
                dict(r)
                for r in conn.execute(
                    "SELECT size, qty FROM inventory WHERE sku = ? ORDER BY size",
                    (sku,),
                ).fetchall()
            ],
        }

    if size and qty_needed:
        on_hand = rows[0]["qty"]
        result["qty_needed"] = qty_needed
        result["on_hand"] = on_hand
        result["can_fill"] = on_hand >= qty_needed
        result["shortfall"] = max(0, qty_needed - on_hand)
    return result


@mcp.tool
def list_money_due() -> dict:
    """List everything the shop owes right now, against the cash it has.

    Pulls open invoices and lease rent, dates each one against desk.date_today
    (negative days_until = already overdue), and compares the total to the
    checking balance. Read-only: this tool never moves money and never marks
    anything paid.

    Returns the cash balance, one entry per obligation, the total owed, and
    what would be left if all of them were paid.
    """
    with _conn() as conn:
        today = _today(conn)

        accounts = [
            dict(r)
            for r in conn.execute(
                "SELECT name, balance, date FROM cash_accounts ORDER BY name"
            ).fetchall()
        ]
        cash_total = sum(a["balance"] for a in accounts)

        obligations = []
        for inv in conn.execute(
            "SELECT i.id, i.amount, i.due_date, i.status, i.description, "
            "       i.vendor_id, v.name AS vendor_name "
            "FROM invoices i JOIN vendors v ON v.id = i.vendor_id "
            "WHERE i.status != 'paid' ORDER BY i.due_date"
        ).fetchall():
            days = _days_until(today, inv["due_date"])
            obligations.append(
                {
                    "kind": "invoice",
                    "ref_id": inv["id"],
                    "owed_to": inv["vendor_name"],
                    "vendor_id": inv["vendor_id"],
                    "amount": inv["amount"],
                    "due_date": inv["due_date"],
                    "days_until_due": days,
                    "overdue": days < 0,
                    "status": inv["status"],
                    "description": inv["description"],
                }
            )

        for lease in conn.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due "
            "FROM leases ORDER BY next_due"
        ).fetchall():
            days = _days_until(today, lease["next_due"])
            obligations.append(
                {
                    "kind": "rent",
                    "ref_id": lease["id"],
                    "owed_to": lease["landlord"],
                    "amount": lease["monthly_rent"],
                    "due_date": lease["next_due"],
                    "days_until_due": days,
                    "overdue": days < 0,
                    "space_name": lease["space_name"],
                }
            )

        # Paid-to-date, so a second call after an approved payment is accurate.
        paid = [
            dict(r)
            for r in conn.execute(
                "SELECT id, kind, ref_id, amount, account, paid_at, approved_by "
                "FROM payments ORDER BY id"
            ).fetchall()
        ]

    obligations.sort(key=lambda o: o["days_until_due"])
    total_due = sum(o["amount"] for o in obligations)
    return {
        "date_today": today,
        "accounts": accounts,
        "cash_available": cash_total,
        "obligations": obligations,
        "total_due": total_due,
        "cash_after_paying_all": round(cash_total - total_due, 2),
        "cash_covers_everything": cash_total >= total_due,
        "payments_already_made": paid,
    }


@mcp.tool
def check_vendor_can_ship(sku: str) -> dict:
    """Find who restocks a product and whether anything is blocking them.

    Matches the product to a vendor by vendors.specialty, reports their
    lead_days and the earliest date they could deliver counting from
    desk.date_today, and lists any unpaid invoice for that vendor. A vendor
    will not ship new product while they have an open invoice, so `blocked`
    being true means the restock cannot be promised until that bill is paid.

    If no vendor specialty clearly covers the SKU, returns blocked=None with
    every vendor listed, rather than guessing at a match.
    """
    with _conn() as conn:
        today = _today(conn)

        product = conn.execute(
            "SELECT DISTINCT sku, name FROM inventory WHERE sku = ?", (sku,)
        ).fetchone()
        all_vendors = [
            dict(r)
            for r in conn.execute(
                "SELECT id, name, specialty, lead_days FROM vendors ORDER BY id"
            ).fetchall()
        ]

        if product is None:
            return {
                "sku": sku,
                "matched": False,
                "blocked": None,
                "reason": f"No product with sku={sku!r} in inventory.",
                "vendors": all_vendors,
            }

        word = next(
            (
                specialty_word
                for sku_word, specialty_word in SKU_WORD_TO_SPECIALTY.items()
                if sku_word in sku.upper()
            ),
            None,
        )
        if word is None:
            return {
                "sku": sku,
                "product_name": product["name"],
                "matched": False,
                "blocked": None,
                "reason": (
                    f"No vendor specialty in the database clearly covers "
                    f"{sku!r}. Listing all vendors instead of guessing."
                ),
                "vendors": all_vendors,
            }

        vendors = [
            dict(r)
            for r in conn.execute(
                "SELECT id, name, specialty, lead_days FROM vendors "
                "WHERE LOWER(specialty) LIKE ? ORDER BY lead_days",
                (f"%{word}%",),
            ).fetchall()
        ]
        if not vendors:
            return {
                "sku": sku,
                "product_name": product["name"],
                "matched": False,
                "blocked": None,
                "reason": (
                    f"Nothing in vendors.specialty matches {word!r} for {sku!r}."
                ),
                "vendors": all_vendors,
            }

        for vendor in vendors:
            unpaid = [
                dict(r)
                for r in conn.execute(
                    "SELECT id, amount, due_date, status, description "
                    "FROM invoices WHERE vendor_id = ? AND status != 'paid' "
                    "ORDER BY due_date",
                    (vendor["id"],),
                ).fetchall()
            ]
            for invoice in unpaid:
                invoice["days_until_due"] = _days_until(
                    today, invoice["due_date"]
                )
                invoice["overdue"] = invoice["days_until_due"] < 0
            vendor["unpaid_invoices"] = unpaid
            vendor["blocked"] = bool(unpaid)
            vendor["amount_to_unblock"] = round(
                sum(i["amount"] for i in unpaid), 2
            )
            ship_by = date.fromisoformat(today) + timedelta(
                days=vendor["lead_days"]
            )
            vendor["earliest_delivery_if_unblocked"] = ship_by.isoformat()

    return {
        "sku": sku,
        "product_name": product["name"],
        "matched": True,
        "date_today": today,
        "vendors": vendors,
        "blocked": all(v["blocked"] for v in vendors),
    }


# ---------------------------------------------------------------------------
# Problem 5 additions: the tools the agent team needs to actually work the
# board. Everything the agents know about the shop comes through here.
# ---------------------------------------------------------------------------

# The provided schema has nowhere to park a payment that has been proposed but
# not yet approved by a human. Rather than write pending rows into `payments`
# (which would make an unapproved request look like money that moved), the
# working copy gets one extra table. The original campus_customs.db is never
# touched, so a reset still gives the shop exactly as it was handed out.
def _ensure_schema() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                ref_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                reason TEXT,
                requested_by TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                status TEXT NOT NULL,
                decided_by TEXT,
                decided_at TEXT,
                payment_id INTEGER
            )
            """
        )


_ensure_schema()


def _owed(conn: sqlite3.Connection, kind: str, ref_id: int) -> dict | None:
    """What the shop actually owes for this reference, straight from the DB."""
    if kind == "invoice":
        row = conn.execute(
            "SELECT i.id, i.amount, i.status, i.due_date, v.name AS payee "
            "FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?",
            (ref_id,),
        ).fetchone()
    elif kind == "rent":
        row = conn.execute(
            "SELECT id, monthly_rent AS amount, 'open' AS status, "
            "       next_due AS due_date, landlord AS payee FROM leases WHERE id = ?",
            (ref_id,),
        ).fetchone()
    else:
        return None
    return dict(row) if row else None


@mcp.tool
def list_open_tickets(ticket_id: int = 0) -> dict:
    """Read the ticket board.

    Returns every open ticket, each with the rows its pointers reach: the
    inventory line for its sku+size, the lease it names, the invoice it names.
    Pass `ticket_id` to pull one ticket by id regardless of status.

    This is the only way to see the board — no other tool reads `tickets`.
    """
    with _conn() as conn:
        today = _today(conn)
        if ticket_id:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at"
            ).fetchall()

        tickets = []
        for r in rows:
            t = dict(r)
            if t.get("sku"):
                stock = conn.execute(
                    "SELECT sku, name, size, qty, location FROM inventory "
                    "WHERE sku = ? AND size = ?",
                    (t["sku"], t.get("size") or ""),
                ).fetchone()
                t["inventory_for_requested_size"] = dict(stock) if stock else None
            if t.get("lease_id"):
                lease = conn.execute(
                    "SELECT * FROM leases WHERE id = ?", (t["lease_id"],)
                ).fetchone()
                t["lease"] = dict(lease) if lease else None
            if t.get("invoice_id"):
                inv = conn.execute(
                    "SELECT * FROM invoices WHERE id = ?", (t["invoice_id"],)
                ).fetchone()
                t["invoice"] = dict(inv) if inv else None
            tickets.append(t)

    return {"date_today": today, "count": len(tickets), "tickets": tickets}


@mcp.tool
def quote_discount(sku: str, qty: int, proposed_unit_price: float) -> dict:
    """Price a discount request against what the product actually costs.

    Reads `pricing` for unit_cost and list_price, then works out the margin at
    the proposed price: per unit, across the whole order, as a percentage, and
    how far the proposal sits below list. `below_cost` is the bright line — a
    price under unit_cost loses money on every unit sold.

    Returns the numbers only. Whether a discount is acceptable is a judgment
    for the Accounting agent and the Boss, not for this tool.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()
        if row is None:
            known = [
                r["sku"]
                for r in conn.execute("SELECT sku FROM pricing ORDER BY sku").fetchall()
            ]
            return {
                "found": False,
                "sku": sku,
                "reason": f"No pricing row for sku={sku!r}.",
                "known_skus": known,
            }
        price = dict(row)

    unit_cost, list_price = price["unit_cost"], price["list_price"]
    margin_unit = proposed_unit_price - unit_cost
    return {
        "found": True,
        "sku": sku,
        "qty": qty,
        "unit_cost": unit_cost,
        "list_price": list_price,
        "proposed_unit_price": proposed_unit_price,
        "discount_off_list_pct": round((1 - proposed_unit_price / list_price) * 100, 2),
        "margin_per_unit": round(margin_unit, 2),
        "margin_pct_of_price": (
            round(margin_unit / proposed_unit_price * 100, 2)
            if proposed_unit_price
            else None
        ),
        "order_revenue": round(proposed_unit_price * qty, 2),
        "order_cost": round(unit_cost * qty, 2),
        "order_margin": round(margin_unit * qty, 2),
        "below_cost": proposed_unit_price < unit_cost,
        "revenue_at_list": round(list_price * qty, 2),
    }


@mcp.tool
def request_payment(
    kind: str, ref_id: int, amount: float, reason: str, requested_by: str
) -> dict:
    """Propose a payment. This does NOT move any money.

    Writes a pending request that a human has to approve before a cent leaves
    the account. `kind` is "invoice" or "rent"; `ref_id` is the invoices.id or
    leases.id being paid. The amount is checked against what the database says
    is owed, so a request for an invented figure is refused.

    Returns the request id. Approval happens outside the agent team.
    """
    kind = (kind or "").strip().lower()
    if kind not in {"invoice", "rent"}:
        return {"ok": False, "reason": "kind must be 'invoice' or 'rent'."}

    with _conn() as conn:
        today = _today(conn)
        owed = _owed(conn, kind, ref_id)
        if owed is None:
            return {"ok": False, "reason": f"No {kind} with id {ref_id}."}
        if kind == "invoice" and owed["status"] == "paid":
            return {"ok": False, "reason": f"Invoice {ref_id} is already paid."}
        if round(amount, 2) != round(owed["amount"], 2):
            return {
                "ok": False,
                "reason": (
                    f"Requested {amount} but the database says {owed['amount']} "
                    f"is owed on {kind} {ref_id}. Request the real amount."
                ),
                "amount_owed": owed["amount"],
            }
        dupe = conn.execute(
            "SELECT id FROM payment_requests WHERE kind = ? AND ref_id = ? "
            "AND status = 'pending'",
            (kind, ref_id),
        ).fetchone()
        if dupe:
            return {
                "ok": False,
                "reason": f"Request {dupe['id']} for this {kind} is already pending.",
                "request_id": dupe["id"],
            }
        cash = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()["balance"]
        cur = conn.execute(
            "INSERT INTO payment_requests "
            "(kind, ref_id, amount, reason, requested_by, requested_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'pending')",
            (kind, ref_id, owed["amount"], reason, requested_by, today),
        )
        request_id = cur.lastrowid

    return {
        "ok": True,
        "request_id": request_id,
        "status": "pending_human_approval",
        "kind": kind,
        "ref_id": ref_id,
        "amount": owed["amount"],
        "payee": owed["payee"],
        "cash_before": cash,
        "cash_if_approved": round(cash - owed["amount"], 2),
        "note": "No money has moved. A human must approve this request.",
    }


@mcp.tool
def approve_and_pay(request_id: int, approved_by: str) -> dict:
    """HUMAN ONLY. Approve a pending request and actually move the money.

    This tool is deliberately kept out of every agent's toolset. It is the only
    thing in the system that reduces the cash balance.

    Refuses if the request is not pending, if the approver is blank, or if the
    balance would go negative — no overdrafts. On success it writes a row to
    `payments` stamped with the approver, reduces `cash_accounts.balance`, and
    updates the thing that was paid: an invoice goes to status 'paid', a lease
    rolls `next_due` on by one month.
    """
    if not (approved_by or "").strip():
        return {"ok": False, "reason": "approved_by is required - who approved this?"}

    with _conn() as conn:
        today = _today(conn)
        req = conn.execute(
            "SELECT * FROM payment_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if req is None:
            return {"ok": False, "reason": f"No payment request {request_id}."}
        req = dict(req)
        if req["status"] != "pending":
            return {
                "ok": False,
                "reason": f"Request {request_id} is already {req['status']}.",
            }

        acct = conn.execute(
            "SELECT name, balance FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
        balance = acct["balance"]
        if balance < req["amount"]:
            return {
                "ok": False,
                "reason": (
                    f"Refused: paying {req['amount']} from a balance of {balance} "
                    f"would overdraw the account."
                ),
                "cash_available": balance,
                "amount_requested": req["amount"],
            }

        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, 'checking', ?, ?)",
            (req["kind"], req["ref_id"], req["amount"], today, approved_by.strip()),
        )
        payment_id = cur.lastrowid
        new_balance = round(balance - req["amount"], 2)
        conn.execute(
            "UPDATE cash_accounts SET balance = ?, date = ? WHERE name = 'checking'",
            (new_balance, today),
        )

        if req["kind"] == "invoice":
            conn.execute(
                "UPDATE invoices SET status = 'paid' WHERE id = ?", (req["ref_id"],)
            )
            updated = f"invoices.{req['ref_id']}.status = 'paid'"
        else:
            due = date.fromisoformat(
                conn.execute(
                    "SELECT next_due FROM leases WHERE id = ?", (req["ref_id"],)
                ).fetchone()["next_due"]
            )
            month = due.month + 1
            year = due.year + (month > 12)
            month = month - 12 if month > 12 else month
            next_due = date(year, month, min(due.day, 28)).isoformat()
            conn.execute(
                "UPDATE leases SET next_due = ? WHERE id = ?", (next_due, req["ref_id"])
            )
            updated = f"leases.{req['ref_id']}.next_due = {next_due}"

        conn.execute(
            "UPDATE payment_requests SET status = 'approved', decided_by = ?, "
            "decided_at = ?, payment_id = ? WHERE id = ?",
            (approved_by.strip(), today, payment_id, request_id),
        )

    return {
        "ok": True,
        "payment_id": payment_id,
        "request_id": request_id,
        "approved_by": approved_by.strip(),
        "amount_paid": req["amount"],
        "cash_before": balance,
        "cash_after": new_balance,
        "also_updated": updated,
    }


@mcp.tool
def resolve_ticket(ticket_id: int, resolution: str) -> dict:
    """Close a ticket with the outcome written onto the board.

    Sets status to 'resolved' and appends the resolution to the ticket's notes,
    dated with the shop's today. Refuse-proof: a ticket that is already
    resolved is not reopened or overwritten.
    """
    if not (resolution or "").strip():
        return {"ok": False, "reason": "A resolution is required to close a ticket."}

    with _conn() as conn:
        today = _today(conn)
        row = conn.execute(
            "SELECT id, status, notes FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if row is None:
            return {"ok": False, "reason": f"No ticket {ticket_id}."}
        if row["status"] == "resolved":
            return {"ok": False, "reason": f"Ticket {ticket_id} is already resolved."}

        notes = (row["notes"] or "").rstrip()
        notes = f"{notes}\n[resolved {today}] {resolution.strip()}".strip()
        conn.execute(
            "UPDATE tickets SET status = 'resolved', notes = ? WHERE id = ?",
            (notes, ticket_id),
        )

    return {"ok": True, "ticket_id": ticket_id, "status": "resolved", "notes": notes}


@mcp.tool
def save_draft_message(ticket_id: int, message: str) -> dict:
    """Save a customer message as a draft on the ticket. Nothing is sent.

    There is no email in this shop and no tool that can send one. The draft is
    appended to the ticket's notes so a human can read it on the board and send
    it themselves if they choose.
    """
    if not (message or "").strip():
        return {"ok": False, "reason": "An empty draft is not worth saving."}

    with _conn() as conn:
        today = _today(conn)
        row = conn.execute(
            "SELECT id, requester, notes FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if row is None:
            return {"ok": False, "reason": f"No ticket {ticket_id}."}
        notes = (row["notes"] or "").rstrip()
        notes = (
            f"{notes}\n[draft to {row['requester']} {today}] {message.strip()}"
        ).strip()
        conn.execute("UPDATE tickets SET notes = ? WHERE id = ?", (notes, ticket_id))

    return {
        "ok": True,
        "ticket_id": ticket_id,
        "drafted_to": row["requester"],
        "sent": False,
        "note": "Draft saved to the ticket. Nothing was emailed.",
    }


@mcp.tool
def update_inventory(sku: str, size: str, qty_delta: int, reason: str) -> dict:
    """Adjust units on hand for one sku+size, with a reason on the record.

    Use for real physical movements only — stock allocated to an order, a
    delivery counted in, a miscount corrected. `qty_delta` is the change, so -1
    takes one off the shelf and +12 books a delivery in.

    Refuses to take stock below zero, and refuses a blank reason: an inventory
    change nobody can explain later is worse than no change at all.
    """
    if not (reason or "").strip():
        return {"ok": False, "reason": "A reason is required for any stock change."}

    with _conn() as conn:
        row = conn.execute(
            "SELECT sku, name, size, qty FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
        if row is None:
            return {
                "ok": False,
                "reason": f"No inventory row for sku={sku!r} size={size!r}.",
            }
        before = row["qty"]
        after = before + qty_delta
        if after < 0:
            return {
                "ok": False,
                "reason": (
                    f"Refused: {before} on hand, change of {qty_delta} would leave "
                    f"{after}. Stock cannot go negative."
                ),
                "qty_on_hand": before,
            }
        conn.execute(
            "UPDATE inventory SET qty = ? WHERE sku = ? AND size = ?",
            (after, sku, size),
        )

    return {
        "ok": True,
        "sku": sku,
        "size": size,
        "qty_before": before,
        "qty_after": after,
        "change": qty_delta,
        "reason": reason.strip(),
    }


@mcp.tool
def list_payment_requests(status: str = "pending") -> dict:
    """List payment requests and where each one stands.

    Pass status="pending" (default) for requests still waiting on a human,
    "approved" for ones that were approved and paid, or "all" for everything.
    Use this before raising a request so the same bill is not proposed twice,
    and to see what is still sitting with the human.
    """
    with _conn() as conn:
        today = _today(conn)
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM payment_requests ORDER BY id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM payment_requests WHERE status = ? ORDER BY id",
                (status,),
            ).fetchall()
        requests = []
        for r in rows:
            req = dict(r)
            owed = _owed(conn, req["kind"], req["ref_id"])
            req["payee"] = owed["payee"] if owed else None
            requests.append(req)
        cash = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()["balance"]

    pending_total = sum(r["amount"] for r in requests if r["status"] == "pending")
    return {
        "date_today": today,
        "status_filter": status,
        "count": len(requests),
        "requests": requests,
        "pending_total": round(pending_total, 2),
        "cash_available": cash,
        "cash_if_all_pending_approved": round(cash - pending_total, 2),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Campus Customs MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Serve Streamable HTTP on port 8002 (keeps FastAPI free on 8000)",
    )
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="http", host="127.0.0.1", port=8002)
    else:
        mcp.run()
