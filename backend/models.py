"""Data types for the Campus Customs agent team.

Two kinds of thing live here: the structured outputs agents must return (so the
runner can read a decision instead of parsing prose), and the dependencies
carried through a run (run id, delegation depth, who the human approver is).

Shop facts are deliberately NOT modelled here. Stock levels, prices, cash and
tickets live in the database and reach the agents only through MCP tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


class SpecialistReport(BaseModel):
    """What any specialist hands back to whoever asked."""

    findings: str = Field(
        description="What the tools actually said. Facts only, no speculation."
    )
    recommendation: str = Field(
        description="What this specialist thinks should happen, and why."
    )
    blocked_by: str = Field(
        default="",
        description="What stops this from being done now, if anything. Empty if nothing.",
    )
    tools_used: list[str] = Field(
        default_factory=list, description="MCP tools called while answering."
    )
    needs_human_approval: bool = Field(
        default=False,
        description="True if acting on this would move money or need a human decision.",
    )


class TicketDecision(BaseModel):
    """The Boss's final word on one ticket."""

    ticket_id: int
    decision: str = Field(description="What the shop is doing about this ticket.")
    reasoning: str = Field(description="Why, including which facts drove it.")
    delegated_to: list[str] = Field(
        default_factory=list, description="Specialists consulted on this ticket."
    )
    payment_requests: list[int] = Field(
        default_factory=list,
        description="Ids of payment requests raised. These are pending until a human approves.",
    )
    resolved: bool = Field(
        default=False, description="True only if resolve_ticket was called and succeeded."
    )
    awaiting_human: str = Field(
        default="",
        description="What a human still has to do before this ticket is finished.",
    )


@dataclass
class ShopPolicy:
    """Shop rules that are judgment calls, not database facts.

    These are set by the shop owner, not invented by an agent. They are passed
    into the prompts so every agent applies the same rule.
    """

    discount_floor_rule: str = (
        "Never price below unit cost. Any price under a 25% gross margin needs "
        "the Boss to sign off explicitly."
    )
    partial_fulfilment: str = (
        "Partial fulfilment is allowed: ship what is on hand now and the rest on "
        "restock, as long as the customer is told both dates."
    )
    payment_priority: str = (
        "Rent comes before vendor bills on principle. When cash covers both, pay "
        "them in the same approval batch so no vendor stays blocked."
    )
    human_approver: str = "Rias Reed"


@dataclass
class RunDeps:
    """Carried through every agent and every delegation in one run."""

    run_id: str
    policy: ShopPolicy = field(default_factory=ShopPolicy)
    depth: int = 0
    chain: tuple[str, ...] = ()

    def descend(self, to_agent: str) -> "RunDeps":
        """Deps for a delegated call, one level deeper."""
        return RunDeps(
            run_id=self.run_id,
            policy=self.policy,
            depth=self.depth + 1,
            chain=self.chain + (to_agent,),
        )
