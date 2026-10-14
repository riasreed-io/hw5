"""Shared shop operations, used by both the CLI runner and the FastAPI app.

Everything here goes through the MCP server. There is no second set of shop
tools: when this module needs a fact or a write, it opens an MCP client and
calls the same tool an agent would call.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

import audit
from agents import LIMITS, MCP_SERVER, build_team, model_label
from models import RunDeps, ShopPolicy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = ROOT / "data" / "campus_customs_new.db"

# One ticket at a time. Two runs at once would interleave their writes to the
# same database and their lines in the audit trail.
RUN_LOCK = asyncio.Lock()

TICKET_TASK = """Work ticket {ticket_id} to a decision.

The ticket as it stands on the board:
{ticket}

Read it, pull in whichever specialists own the parts you cannot answer
yourself, and decide what Campus Customs is doing about it. Close it with
resolve_ticket if the work is genuinely finished or if the only thing left is a
human approving a payment - say which in the resolution. If money needs to
move, make sure a payment request exists and tell me its id."""


def mcp_client() -> Client:
    """A direct MCP client for non-agent steps. Same server the agents use."""
    return Client(
        StdioTransport(command=sys.executable, args=[str(MCP_SERVER)], cwd=str(ROOT))
    )


async def call_tool(name: str, **kwargs: Any) -> dict:
    async with mcp_client() as client:
        result = await client.call_tool(name, kwargs)
        return json.loads(result.content[0].text)


def reset_database() -> dict:
    """Copy the pristine database over the working copy, as the spec asks."""
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    return {"reset": True, "from": ORIGINAL_DB.name, "to": WORKING_DB.name}


async def board(ticket_id: int = 0) -> dict:
    """Every ticket and its status. Tickets of any status, not just open."""
    open_board = await call_tool("list_open_tickets", ticket_id=ticket_id)
    if ticket_id:
        return open_board
    # list_open_tickets returns only open ones; the dashboard wants all three
    # and their state, so pull each id it knows about as well.
    seen = {t["id"]: t for t in open_board["tickets"]}
    for tid in (101, 102, 103):
        if tid not in seen:
            one = await call_tool("list_open_tickets", ticket_id=tid)
            for t in one["tickets"]:
                seen[t["id"]] = t
    tickets = [seen[k] for k in sorted(seen)]
    return {
        "date_today": open_board["date_today"],
        "count": len(tickets),
        "open": sum(1 for t in tickets if t["status"] == "open"),
        "resolved": sum(1 for t in tickets if t["status"] == "resolved"),
        "tickets": tickets,
    }


async def cash() -> dict:
    """The checking balance, with what is pending against it."""
    requests = await call_tool("list_payment_requests", status="all")
    return {
        "account": "checking",
        "balance": requests["cash_available"],
        "date_today": requests["date_today"],
        "pending_total": requests["pending_total"],
        "cash_if_all_pending_approved": requests["cash_if_all_pending_approved"],
    }


async def payment_requests(status: str = "pending") -> dict:
    return await call_tool("list_payment_requests", status=status)


async def approve(request_id: int, approved_by: str) -> dict:
    """The human step. The only path in this codebase that moves money."""
    result = await call_tool(
        "approve_and_pay", request_id=request_id, approved_by=approved_by
    )
    audit.record(
        audit.new_run_id(),
        "human_approval",
        actor=approved_by,
        request_id=request_id,
        approved=result.get("ok", False),
        outcome=audit.preview(result),
    )
    return result


async def run_ticket(ticket_id: int, policy: ShopPolicy | None = None) -> dict:
    """Run the agent team on one ticket. Returns the Boss's decision."""
    policy = policy or ShopPolicy()
    async with RUN_LOCK:
        one = await call_tool("list_open_tickets", ticket_id=ticket_id)
        if not one["tickets"]:
            raise ValueError(f"No ticket {ticket_id}")
        ticket = one["tickets"][0]

        run_id = audit.new_run_id()
        team = build_team(run_id, policy)
        boss = team["boss"]

        audit.record(
            run_id,
            "run_start",
            model=model_label(),
            open_tickets=[ticket_id],
            shop_date=one["date_today"],
            started_by="api",
        )
        audit.record(run_id, "agent_start", agent="boss", ticket_id=ticket_id, depth=0)

        async with boss:
            result = await boss.run(
                TICKET_TASK.format(
                    ticket_id=ticket_id, ticket=json.dumps(ticket, indent=2)
                ),
                deps=RunDeps(run_id=run_id, policy=policy, chain=("boss",)),
                usage_limits=LIMITS,
            )

        usage = result.usage
        decision = result.output
        audit.record(
            run_id,
            "agent_end",
            agent="boss",
            ticket_id=ticket_id,
            depth=0,
            decision=audit.preview(decision.decision),
            reasoning=audit.preview(decision.reasoning),
            delegated_to=decision.delegated_to,
            payment_requests=decision.payment_requests,
            resolved=decision.resolved,
            awaiting_human=audit.preview(decision.awaiting_human),
            requests=usage.requests,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        )
        audit.record(run_id, "run_end", tickets_decided=1, run_source="api")

        return {
            "run_id": run_id,
            "ticket_id": ticket_id,
            "decision": decision.model_dump(),
            "usage": {
                "requests": usage.requests,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
        }


def recent_events(limit: int = 50, run_id: str = "") -> dict:
    """The tail of the audit trail: what each agent said and which tools ran."""
    entries = audit.read_trail()
    if run_id:
        entries = [e for e in entries if e.get("run_id") == run_id]
    tail = entries[-limit:] if limit else entries
    return {
        "total_entries": len(entries),
        "returned": len(tail),
        "events": list(reversed(tail)),
    }
