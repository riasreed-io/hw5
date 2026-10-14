"""Run the Campus Customs agent team over the open tickets, from the terminal.

    python backend/run_tickets.py --reset            # fresh board, agents only
    python backend/run_tickets.py --reset --approve  # ... then approve payments

Same two phases as the API in main.py, and the same service layer underneath.
Agents raise payment requests; nothing in the team can approve one. The
approval phase is the human step and only runs when a person passes --approve.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit  # noqa: E402
import service  # noqa: E402
from agents import model_label  # noqa: E402
from models import ShopPolicy  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Campus Customs agent team")
    parser.add_argument("--reset", action="store_true", help="restore the working DB first")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="after the agents run, approve pending payments as the shop owner",
    )
    parser.add_argument(
        "--ticket", type=int, default=0, help="run one ticket instead of all open ones"
    )
    args = parser.parse_args()

    if args.reset:
        print(service.reset_database())

    policy = ShopPolicy()
    print(f"model {model_label()} | approver {policy.human_approver}")

    board = await service.board()
    todo = (
        [args.ticket]
        if args.ticket
        else [t["id"] for t in board["tickets"] if t["status"] == "open"]
    )

    decisions = []
    for ticket_id in todo:
        result = await service.run_ticket(ticket_id, policy)
        decision, usage = result["decision"], result["usage"]
        decisions.append(decision)
        print(f"\n--- ticket {ticket_id} ---")
        print(decision["decision"])
        print(f"[awaiting human] {decision['awaiting_human'] or 'nothing'}")
        print(f"[tokens] {usage['total_tokens']} over {usage['requests']} requests")

    if args.approve:
        pending = await service.payment_requests("pending")
        print(
            f"\n=== human approval: {pending['count']} pending, "
            f"{pending['pending_total']} against {pending['cash_available']} cash ==="
        )
        for req in pending["requests"]:
            print(
                f"  request {req['id']}: {req['kind']} {req['ref_id']} "
                f"{req['amount']} to {req['payee']}"
            )
            result = await service.approve(req["id"], policy.human_approver)
            print(
                f"    -> {'PAID' if result.get('ok') else 'REFUSED: ' + result.get('reason', '')}"
            )

    print(f"\ndone. audit trail: {audit.AUDIT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
