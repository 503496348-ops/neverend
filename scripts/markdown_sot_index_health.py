"""Markdown source-of-truth index health for memory cards.

Checks vault notes used as durable memory SoT for:
- missing protocol frontmatter (clients / status / supersedes / cognitive_type)
- active notes that still claim to supersede other active notes
- orphan protocol lineage (dangling supersedes)

Read-only. Complements vault_index link health; does not mutate the vault.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
PROTOCOL_FIELDS = ("clients", "status", "supersedes", "cognitive_type")
ACTIVE = frozenset({"active", "current", "hot", "ok", ""})
SUPERSEDED = frozenset({"superseded", "archived", "retired", "stale"})


@dataclass
class NoteProtocol:
    path: str
    title: str
    fields: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return str(self.fields.get("status", "") or "").strip().lower()

    @property
    def memory_id(self) -> str:
        return str(self.fields.get("id") or self.fields.get("memory_id") or Path(self.path).stem)


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [p.strip().strip("'\"") for p in inner.split(",") if p.strip().strip("'\"")]
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text


def parse_frontmatter(text: str) -> dict[str, Any]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, Any] = {}
    current: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if current and re.match(r"^\s+-\s+", line):
            item = re.sub(r"^\s+-\s+", "", line).strip().strip("'\"")
            bucket = fields.setdefault(current, [])
            if not isinstance(bucket, list):
                bucket = [bucket]
                fields[current] = bucket
            bucket.append(item)
            continue
        if ":" not in line:
            current = None
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"", "|", ">"}:
            fields[key] = []
            current = key
        else:
            fields[key] = _parse_scalar(value)
            current = None
    return fields


def iter_markdown(vault: Path) -> Iterable[Path]:
    skip = {".git", ".obsidian", ".trash", "node_modules", "__pycache__"}
    for path in sorted(vault.rglob("*.md")):
        if any(part in skip for part in path.parts):
            continue
        yield path


def audit_markdown_sot(vault: str | Path) -> dict[str, Any]:
    root = Path(vault)
    notes: list[NoteProtocol] = []
    for path in iter_markdown(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        fields = parse_frontmatter(text)
        title = str(fields.get("title") or path.stem)
        notes.append(NoteProtocol(path=str(path.relative_to(root)), title=title, fields=fields))

    by_id = {n.memory_id: n for n in notes}
    findings: list[dict[str, str]] = []
    protocol_notes = 0
    for note in notes:
        has_any = any(k in note.fields for k in PROTOCOL_FIELDS)
        if not has_any:
            continue
        protocol_notes += 1
        missing = [f for f in PROTOCOL_FIELDS if f not in note.fields]
        if missing:
            findings.append(
                {
                    "code": "missing_protocol_fields",
                    "path": note.path,
                    "detail": f"missing: {', '.join(missing)}",
                }
            )
        for target in note.fields.get("supersedes") or []:
            tid = Path(str(target)).stem
            other = by_id.get(tid) or by_id.get(str(target))
            if other is None:
                findings.append(
                    {
                        "code": "dangling_supersedes",
                        "path": note.path,
                        "detail": f"unknown target {target}",
                    }
                )
            elif note.status in ACTIVE and other.status in ACTIVE:
                findings.append(
                    {
                        "code": "active_supersedes_active",
                        "path": note.path,
                        "detail": f"both active: {note.memory_id} -> {other.memory_id}",
                    }
                )

    high = sum(1 for f in findings if f["code"] == "active_supersedes_active")
    return {
        "ok": high == 0,
        "vault": str(root),
        "note_count": len(notes),
        "protocol_note_count": protocol_notes,
        "findings": findings,
        "summary": {
            "findings": len(findings),
            "active_conflicts": high,
            "missing_fields": sum(1 for f in findings if f["code"] == "missing_protocol_fields"),
            "dangling": sum(1 for f in findings if f["code"] == "dangling_supersedes"),
        },
        "protocol_fields": list(PROTOCOL_FIELDS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Markdown SoT memory protocol fields")
    parser.add_argument("vault", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = audit_markdown_sot(args.vault)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print(
            f"markdown SoT ok={result['ok']} notes={result['note_count']} "
            f"protocol_notes={result['protocol_note_count']} conflicts={s['active_conflicts']}"
        )
        for f in result["findings"]:
            print(f"- {f['code']}: {f['detail']} ({f['path']})")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
