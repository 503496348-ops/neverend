"""Build durable timelines from NeverEnd vault sync audit data."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(frozen=True)
class TimelineEvent:
    timestamp: str
    item_id: str
    event_type: str
    actor: str
    summary: str
    source: str = "runtime"


def normalize_flow_entries(item: dict) -> list[TimelineEvent]:
    item_id = item.get("id") or item.get("item_id") or item.get("task_id") or "unknown"
    events: list[TimelineEvent] = []
    for entry in item.get("flow_log") or []:
        events.append(TimelineEvent(
            timestamp=entry.get("timestamp") or entry.get("ts") or entry.get("at") or datetime.now(timezone.utc).isoformat(),
            item_id=item_id,
            event_type="state_transition",
            actor=entry.get("actor") or entry.get("agent") or "system",
            summary=f"{entry.get('source') or entry.get('from')} -> {entry.get('target') or entry.get('to')}: {entry.get('reason') or entry.get('remark') or ''}".strip(),
        ))
    return sorted(events, key=lambda e: e.timestamp)


def timeline_to_jsonable(events: list[TimelineEvent]) -> list[dict]:
    return [asdict(e) for e in events]
