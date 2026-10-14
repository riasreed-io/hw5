"""The Campus Customs agent team.

Five agents — Boss, Inventory, Accounting, Facilities, Customer Service — all
on gpt-6-luna through Portkey, all reading the shop through the MCP server and
nothing else.

Full connectivity: every agent carries an `ask_<colleague>` tool for each of
the other four, so any agent can delegate to any other. Depth is capped so a
chain cannot run away, and token usage is shared across the whole run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPToolset
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.usage import UsageLimits

import audit
from models import AgentName, RunDeps, ShopPolicy, SpecialistReport, TicketDecision

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPTS = HERE / "prompts"
MCP_SERVER = ROOT / "mcp_server" / "server.py"

PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# The assignment allows exactly one model. Anything else costs points, so this
# is enforced in code rather than trusted to a config file.
REQUIRED_MODEL = "gpt-6-luna"

# The Portkey gateway refuses function tools on gpt-6-luna unless reasoning
# effort is switched off: "Function tools with reasoning_effort are not
# supported for gpt-6-luna-global in /v1/chat/completions". Every agent here
# uses tools, so this setting is not optional.
MODEL_SETTINGS = OpenAIChatModelSettings(openai_reasoning_effort="none")

# --- Token discipline -------------------------------------------------------
# Five agents that can all call each other is how a run quietly turns into a
# five-figure token bill. These are the ceilings for one ticket.
MAX_DELEGATION_DEPTH = 2        # Boss -> specialist -> one more specialist
LIMITS = UsageLimits(
    request_limit=60,           # model calls per ticket, across the whole chain
    tool_calls_limit=90,        # MCP + delegation calls per ticket
    total_tokens_limit=200_000,
)

# --- Which tools each agent may touch --------------------------------------
# approve_and_pay appears in NO list. It is the only tool that moves money, and
# it is reserved for the human approval step in run_tickets.py.
TOOLS_BY_AGENT: dict[AgentName, set[str]] = {
    "boss": {"list_open_tickets", "resolve_ticket"},
    "inventory": {
        "list_open_tickets",
        "check_stock",
        "check_vendor_can_ship",
        "update_inventory",
    },
    "accounting": {
        "list_open_tickets",
        "list_money_due",
        "quote_discount",
        "check_vendor_can_ship",
        "request_payment",
        "list_payment_requests",
    },
    "facilities": {
        "list_open_tickets",
        "list_money_due",
        "request_payment",
        "list_payment_requests",
    },
    "customer_service": {"list_open_tickets", "check_stock", "save_draft_message"},
}

ROLE_TITLES: dict[AgentName, str] = {
    "boss": "Boss",
    "inventory": "Inventory",
    "accounting": "Accounting",
    "facilities": "Facilities",
    "customer_service": "Customer Service",
}


def load_environment() -> None:
    """Look for .env beside this file, then the homework root, then the course root."""
    for candidate in (HERE / ".env", ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)


def build_model() -> OpenAIChatModel:
    """Every agent in this homework uses gpt-6-luna through Portkey."""
    load_environment()
    key = (os.getenv("PORTKEY_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "No PORTKEY_API_KEY found. Copy .env.example to .env and add your key."
        )
    model_name = (os.getenv("CAMPUS_CUSTOMS_MODEL") or REQUIRED_MODEL).strip()
    if model_name != REQUIRED_MODEL:
        raise RuntimeError(
            f"This assignment permits {REQUIRED_MODEL} only, got {model_name!r}."
        )
    return OpenAIChatModel(
        model_name, provider=OpenAIProvider(api_key=key, base_url=PORTKEY_BASE_URL)
    )


def model_label() -> str:
    load_environment()
    return f"{os.getenv('CAMPUS_CUSTOMS_MODEL') or REQUIRED_MODEL} (via Portkey)"


def read_prompt(name: AgentName) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def _shop_rules(policy: ShopPolicy) -> str:
    """Rules every agent gets, appended to its own prompt."""
    return f"""

---

# Shop policy for this run

These are the owner's rules, not yours to change:

- **Discounts.** {policy.discount_floor_rule}
- **Partial orders.** {policy.partial_fulfilment}
- **Paying bills.** {policy.payment_priority}
- **Approval.** Only a human approves a payment. The approver on record for
  this shop is {policy.human_approver}. No agent on this team has a tool that
  can move money, by design — the most you can do is raise a request.
"""


def build_toolset(run_id: str) -> MCPToolset:
    """One MCP connection for the whole team, with every call written to the trail."""

    async def log_tool_call(
        ctx: RunContext[RunDeps], call_tool: CallToolFunc, name: str, args: dict[str, Any]
    ):
        caller = ctx.deps.chain[-1] if ctx.deps.chain else "boss"
        result = await call_tool(name, args)
        audit.record(
            ctx.deps.run_id,
            "mcp_tool_call",
            agent=caller,
            depth=ctx.deps.depth,
            tool=name,
            args=audit.preview(args),
            result=audit.preview(result),
        )
        return result

    client = Client(
        StdioTransport(command=sys.executable, args=[str(MCP_SERVER)], cwd=str(ROOT))
    )
    return MCPToolset(client, process_tool_call=log_tool_call)


def build_team(run_id: str, policy: ShopPolicy | None = None) -> dict[AgentName, Agent]:
    """Build all five agents, wired to each other and to the MCP server."""
    policy = policy or ShopPolicy()
    model = build_model()
    toolset = build_toolset(run_id)
    rules = _shop_rules(policy)

    team: dict[AgentName, Agent] = {}
    for name, allowed in TOOLS_BY_AGENT.items():
        def only_mine(ctx: RunContext[RunDeps], td: ToolDefinition, allowed=allowed) -> bool:
            return td.name in allowed

        team[name] = Agent(
            model,
            deps_type=RunDeps,
            output_type=TicketDecision if name == "boss" else SpecialistReport,
            toolsets=[toolset.filtered(only_mine)],
            instructions=read_prompt(name) + rules,
            model_settings=MODEL_SETTINGS,
            name=name,
            retries=2,
        )

    _wire_delegation(team)
    return team


def _wire_delegation(team: dict[AgentName, Agent]) -> None:
    """Give every agent a way to ask every other agent. Full connectivity."""
    for caller in team:
        for colleague in team:
            if colleague == caller:
                continue
            _attach_ask_tool(team, caller, colleague)


def _attach_ask_tool(
    team: dict[AgentName, Agent], caller: AgentName, colleague: AgentName
) -> None:
    title = ROLE_TITLES[colleague]

    async def ask(ctx: RunContext[RunDeps], question: str) -> str:
        """Ask a colleague for help and return what they say."""
        if ctx.deps.depth >= MAX_DELEGATION_DEPTH:
            audit.record(
                ctx.deps.run_id,
                "delegation_refused",
                frm=caller,
                to=colleague,
                depth=ctx.deps.depth,
                reason="delegation depth limit reached",
            )
            return (
                f"Delegation limit reached (depth {ctx.deps.depth}). Answer with what "
                f"you already know, or hand the open question back to the Boss."
            )

        audit.record(
            ctx.deps.run_id,
            "delegation_start",
            frm=caller,
            to=colleague,
            depth=ctx.deps.depth + 1,
            question=audit.preview(question),
        )
        result = await team[colleague].run(
            question,
            deps=ctx.deps.descend(colleague),
            usage=ctx.usage,
            usage_limits=LIMITS,
        )
        report = result.output
        audit.record(
            ctx.deps.run_id,
            "delegation_end",
            frm=caller,
            to=colleague,
            depth=ctx.deps.depth + 1,
            findings=audit.preview(getattr(report, "findings", report)),
            recommendation=audit.preview(getattr(report, "recommendation", "")),
            blocked_by=getattr(report, "blocked_by", ""),
            needs_human_approval=getattr(report, "needs_human_approval", False),
            tokens=result.usage.total_tokens,
        )
        return report.model_dump_json() if hasattr(report, "model_dump_json") else str(report)

    ask.__name__ = f"ask_{colleague}"
    ask.__doc__ = (
        f"Ask the {title} agent. Use this instead of guessing about anything "
        f"{title} owns. Give them the ticket number and the specific question; "
        f"they answer with findings, a recommendation, and what is blocking it."
    )
    team[caller].tool(ask)
