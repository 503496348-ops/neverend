"""Real-vault sync acceptance harness for Markdown knowledge stores."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class VaultFileState:
    relative_path: str
    digest: str
    bytes: int


def snapshot_vault(root: str | Path) -> dict[str, VaultFileState]:
    base = Path(root)
    states: dict[str, VaultFileState] = {}
    for path in sorted(base.rglob("*.md")):
        if ".trash" in path.parts:
            continue
        data = path.read_bytes()
        rel = path.relative_to(base).as_posix()
        states[rel] = VaultFileState(rel, sha256(data).hexdigest(), len(data))
    return states


def compare_snapshots(before: Mapping[str, VaultFileState], after: Mapping[str, VaultFileState]) -> dict[str, list[str]]:
    before_keys = set(before)
    after_keys = set(after)
    changed = sorted(key for key in before_keys & after_keys if before[key].digest != after[key].digest)
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "changed": changed,
        "unchanged": sorted(key for key in before_keys & after_keys if key not in changed),
    }


def detect_sync_conflicts(root: str | Path) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    for path in Path(root).rglob("*.md"):
        lower_name = path.name.lower()
        if "conflict" in lower_name or "sync-conflict" in lower_name:
            conflicts.append({"path": path.as_posix(), "reason": "conflict_marker_in_filename"})
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "<<<<<<<" in text and ">>>>>>>" in text:
            conflicts.append({"path": path.as_posix(), "reason": "merge_marker_in_content"})
    return conflicts


def evaluate_sync_acceptance(source: str | Path, replica: str | Path) -> dict[str, object]:
    source_snapshot = snapshot_vault(source)
    replica_snapshot = snapshot_vault(replica)
    diff = compare_snapshots(source_snapshot, replica_snapshot)
    conflicts = detect_sync_conflicts(replica)
    passed = not diff["added"] and not diff["removed"] and not diff["changed"] and not conflicts
    return {
        "passed": passed,
        "source_files": len(source_snapshot),
        "replica_files": len(replica_snapshot),
        "diff": diff,
        "conflicts": conflicts,
    }
