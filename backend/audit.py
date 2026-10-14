"""Append-only audit trail for the Campus Customs agent team.

Every step of every run is appended to `output/audit_trail.json` as one JSON
object per line (JSON Lines). The file is opened in append mode and never read,
rewritten or truncated, so:

  * a crash halfway through a write loses at most the line being written,
  * two agents writing at once cannot interleave into a corrupt array, and
  * the trail from earlier runs survives the next run, as the assignment asks.

A single JSON array would have to be parsed and rewritten on every append,
which is neither append-only nor crash-safe. The extension stays `.json`
because that is the filename the assignment specifies; each line is valid JSON
on its own, and `read_trail()` below loads the whole file.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"

# Enough of an argument or a result to see what happened, without pasting the
# whole ticket board into every line.
PREVIEW_CHARS = 400

_lock = threading.Lock()


def new_run_id() -> str:
    """Short id so every line of one run can be pulled back out together."""
    return f"run-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"


def preview(value: Any, limit: int = PREVIEW_CHARS) -> str:
    """A short, readable stand-in for an argument or a tool result."""
    if value is None:
        return ""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def record(run_id: str, event: str, **fields: Any) -> dict:
    """Append one step to the trail and return what was written."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": run_id,
        "event": event,
        **fields,
    }
    line = json.dumps(entry, default=str, ensure_ascii=False)
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return entry


def read_trail(path: Path | None = None) -> list[dict]:
    """Every entry ever written, oldest first. Bad lines are skipped, not fatal."""
    path = path or AUDIT_PATH
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
