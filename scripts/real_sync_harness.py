"""Deterministic sync harness for note-vault roundtrip verification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json


@dataclass(frozen=True)
class VaultProbe:
    relative_path: str
    sha256: str
    size: int


def snapshot_vault(root: str | Path) -> list[VaultProbe]:
    root = Path(root)
    probes: list[VaultProbe] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            data = path.read_bytes()
            probes.append(VaultProbe(str(path.relative_to(root)), hashlib.sha256(data).hexdigest(), len(data)))
    return probes


def compare_snapshots(before: list[VaultProbe], after: list[VaultProbe]) -> dict[str, list[str]]:
    b = {p.relative_path: p for p in before}
    a = {p.relative_path: p for p in after}
    return {
        "added": sorted(set(a) - set(b)),
        "removed": sorted(set(b) - set(a)),
        "changed": sorted(path for path in set(a) & set(b) if a[path].sha256 != b[path].sha256),
    }


def write_manifest(path: str | Path, probes: list[VaultProbe]) -> None:
    payload = [probe.__dict__ for probe in probes]
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
