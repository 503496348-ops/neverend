"""Session asset indexing for NeverEnd vault-backed conversations."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

@dataclass(frozen=True)
class BridgeSessionAsset:
    scope_id: str
    agent: str
    cwd: str
    policy_fingerprint: str
    transcript_ref: str

    @property
    def asset_id(self) -> str:
        raw = "\x1f".join([self.scope_id, self.agent, self.cwd, self.policy_fingerprint, self.transcript_ref])
        return sha256(raw.encode("utf-8")).hexdigest()[:20]

class BridgeSessionAssetIndex:
    def __init__(self) -> None:
        self._assets: dict[str, BridgeSessionAsset] = {}

    def add(self, asset: BridgeSessionAsset) -> str:
        aid = asset.asset_id
        self._assets[aid] = asset
        return aid

    def by_scope(self, scope_id: str) -> list[BridgeSessionAsset]:
        return [a for a in self._assets.values() if a.scope_id == scope_id]

    def stale_after_policy_change(self, scope_id: str, current_fingerprint: str) -> list[BridgeSessionAsset]:
        return [a for a in self.by_scope(scope_id) if a.policy_fingerprint != current_fingerprint]

def build_markdown_manifest(assets: Iterable[BridgeSessionAsset]) -> str:
    rows = ["| scope | agent | cwd | fingerprint | transcript |", "|---|---|---|---|---|"]
    for a in assets:
        rows.append(f"| {a.scope_id} | {a.agent} | {a.cwd} | {a.policy_fingerprint} | {a.transcript_ref} |")
    return "\n".join(rows) + "\n"
