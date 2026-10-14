"""FastAPI backend for the Campus Customs dashboard.

Start it from the backend/ folder:

    uvicorn main:app --reload --port 8000

The React dashboard in the next problem calls these routes. Every shop fact
and every shop change goes through the MCP server underneath - this app has no
database access of its own.

The division that matters: /api/tickets/{id}/run lets the agents prepare work
and raise payment requests, and it cannot move money. /api/payments/{id}/approve
is the human click, and it is the only route that changes cash.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import service  # noqa: E402
from agents import LIMITS, model_label  # noqa: E402
from models import ShopPolicy  # noqa: E402

app = FastAPI(
    title="Campus Customs Operations",
    description="Backend for the agent dashboard. Agents prepare; humans approve.",
    version="1.0.0",
)

# The dashboard runs on a vite dev server on some localhost port.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

POLICY = ShopPolicy()


class ApproveBody(BaseModel):
    approved_by: str = Field(
        default="",
        description="Who approved this. Defaults to the shop's approver on record.",
    )


@app.get("/api/health")
async def health() -> dict:
    """Is the backend up, and which model would a run use."""
    return {
        "ok": True,
        "model": model_label(),
        "approver_on_record": POLICY.human_approver,
        "limits": {
            "requests_per_ticket": LIMITS.request_limit,
            "tool_calls_per_ticket": LIMITS.tool_calls_limit,
            "tokens_per_ticket": LIMITS.total_tokens_limit,
        },
    }


@app.get("/api/tickets")
async def get_tickets() -> dict:
    """The three tickets and whether each one is open or resolved."""
    return await service.board()


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: int) -> dict:
    """One ticket, with the inventory, lease or invoice rows it points at."""
    result = await service.board(ticket_id=ticket_id)
    if not result.get("tickets"):
        raise HTTPException(status_code=404, detail=f"No ticket {ticket_id}")
    return result["tickets"][0]


@app.post("/api/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int) -> dict:
    """Run the agent team on this ticket and return the Boss's decision.

    Takes a while - the Boss reads the board, delegates to specialists, and
    they all call MCP tools. Nothing here can move money; the most the team
    can do is raise a payment request for a human to approve.
    """
    try:
        return await service.run_ticket(ticket_id, POLICY)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/events")
async def get_events(limit: int = 50, run_id: str = "") -> dict:
    """Recent agent events - what each agent said and which tools they used.

    Newest first, so the board can poll this and refresh. Pass `run_id` to see
    a single run, or `limit=0` for the whole trail.
    """
    return service.recent_events(limit=limit, run_id=run_id)


@app.get("/api/payments")
async def get_payments(status: str = "pending") -> dict:
    """Payment requests waiting on a human, with the cash they would consume."""
    return await service.payment_requests(status=status)


@app.post("/api/payments/{request_id}/approve")
async def approve_payment(request_id: int, body: ApproveBody | None = None) -> dict:
    """Approve a prepared payment. This is the route that actually moves cash.

    Agents prepare payments; this is the human click. Refuses to overdraw the
    account, refuses a request that is not pending, and records who approved.
    """
    approver = (body.approved_by if body else "") or POLICY.human_approver
    result = await service.approve(request_id, approver)
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("reason", "refused"))
    return result


@app.get("/api/cash")
async def get_cash() -> dict:
    """The current checking balance from cash_accounts."""
    return await service.cash()


@app.post("/api/reset")
async def reset() -> dict:
    """Restore the working database to the original values for a fresh run."""
    result = service.reset_database()
    result["cash"] = await service.cash()
    return result
