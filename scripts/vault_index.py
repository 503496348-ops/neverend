#!/usr/bin/env python3
"""Markdown vault indexer and link-health reporter for Neverend.

This module keeps the implementation deliberately local-first: it scans a
Markdown/Obsidian vault, extracts note metadata and links, writes an optional
SQLite index, and emits a JSON/Markdown health report.  It does not mutate the
vault and is safe to run before any sync or Wiki upload workflow.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

WIKI_LINK_RE = re.compile(r"!??\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_\-/\u4e00-\u9fff]+)")


@dataclass(frozen=True)
class NoteRecord:
    """Metadata for a single Markdown note."""

    title: str
    path: str
    bytes: int
    lines: int
    headings: int
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class LinkRecord:
    """A resolved or unresolved edge between notes/resources."""

    source: str
    target: str
    kind: str
    raw: str
    resolved: bool


@dataclass
class VaultIndexResult:
    """Structured result returned by :func:`build_vault_index`."""

    vault: str
    generated_at: str
    summary: dict[str, int]
    notes: list[NoteRecord] = field(default_factory=list)
    links: list[LinkRecord] = field(default_factory=list)
    orphan_notes: list[str] = field(default_factory=list)
    broken_links: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "vault": self.vault,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "notes": [asdict(n) for n in self.notes],
            "links": [asdict(l) for l in self.links],
            "orphan_notes": self.orphan_notes,
            "broken_links": self.broken_links,
        }


def iter_markdown_files(vault: Path) -> Iterable[Path]:
    """Yield Markdown files while skipping common generated/cache folders."""

    skip_dirs = {".git", ".obsidian", ".trash", "node_modules", "__pycache__"}
    for path in sorted(vault.rglob("*.md")):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_file():
            yield path


def _strip_frontmatter(text: str) -> tuple[str, dict[str, list[str]]]:
    """Return body text and a tiny YAML-like metadata extraction.

    We intentionally avoid adding PyYAML as a dependency.  This parser only
    handles the fields Neverend needs for vault hygiene: aliases and tags.
    """

    match = FRONTMATTER_RE.match(text)
    if not match:
        return text, {}
    meta_text = match.group(1)
    body = text[match.end() :]
    meta: dict[str, list[str]] = {}
    current_key: str | None = None
    for raw_line in meta_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            parsed_key = key.strip().lower()
            current_key = parsed_key
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                items = [x.strip().strip('"\'') for x in value[1:-1].split(",") if x.strip()]
                meta[parsed_key] = items
            elif value:
                meta[parsed_key] = [value.strip('"\'')]
            else:
                meta[parsed_key] = []
        elif current_key and line.lstrip().startswith("-"):
            meta.setdefault(current_key, []).append(line.lstrip()[1:].strip().strip('"\''))
    return body, meta


def _note_title(path: Path) -> str:
    return path.stem


def _read_note(path: Path, vault: Path) -> NoteRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    body, meta = _strip_frontmatter(text)
    aliases = tuple(sorted(set(meta.get("aliases", []) + meta.get("alias", []))))
    tags = set(meta.get("tags", []) + meta.get("tag", []))
    tags.update(TAG_RE.findall(body))
    return NoteRecord(
        title=_note_title(path),
        path=str(path.relative_to(vault)),
        bytes=path.stat().st_size,
        lines=len(text.splitlines()),
        headings=sum(1 for line in body.splitlines() if line.startswith("#")),
        tags=tuple(sorted(tags)),
        aliases=aliases,
    )


def _extract_links(path: Path, vault: Path, body: str, known_titles: set[str], known_paths: set[str]) -> list[LinkRecord]:
    source = _note_title(path)
    links: list[LinkRecord] = []

    for match in WIKI_LINK_RE.finditer(body):
        target = match.group(1).strip()
        resolved = target in known_titles or f"{target}.md" in known_paths
        links.append(LinkRecord(source=source, target=target, kind="wiki", raw=match.group(0), resolved=resolved))

    for match in MARKDOWN_LINK_RE.finditer(body):
        raw_target = match.group(1).strip()
        if raw_target.startswith(("http://", "https://", "mailto:", "obsidian://", "#")):
            continue
        target_path = (path.parent / raw_target.split("#", 1)[0]).resolve()
        try:
            rel = str(target_path.relative_to(vault.resolve()))
        except ValueError:
            rel = raw_target
        resolved = rel in known_paths or raw_target in known_paths
        links.append(LinkRecord(source=source, target=raw_target, kind="markdown", raw=match.group(0), resolved=resolved))

    return links


def _write_sqlite(path: Path, result: VaultIndexResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            drop table if exists notes;
            drop table if exists links;
            create table notes (
                title text primary key,
                path text not null,
                bytes integer not null,
                lines integer not null,
                headings integer not null,
                tags_json text not null,
                aliases_json text not null
            );
            create table links (
                source text not null,
                target text not null,
                kind text not null,
                raw text not null,
                resolved integer not null
            );
            create index idx_links_source on links(source);
            create index idx_links_target on links(target);
            """
        )
        conn.executemany(
            "insert into notes values (?, ?, ?, ?, ?, ?, ?)",
            [
                (n.title, n.path, n.bytes, n.lines, n.headings, json.dumps(n.tags, ensure_ascii=False), json.dumps(n.aliases, ensure_ascii=False))
                for n in result.notes
            ],
        )
        conn.executemany(
            "insert into links values (?, ?, ?, ?, ?)",
            [(l.source, l.target, l.kind, l.raw, int(l.resolved)) for l in result.links],
        )


def build_vault_index(vault: Path | str, output_db: Path | str | None = None, output_json: Path | str | None = None) -> VaultIndexResult:
    """Scan a Markdown vault and return a structured health index."""

    vault_path = Path(vault).expanduser().resolve()
    if not vault_path.exists() or not vault_path.is_dir():
        raise ValueError(f"vault path is not a directory: {vault_path}")

    md_files = list(iter_markdown_files(vault_path))
    notes = [_read_note(path, vault_path) for path in md_files]
    known_titles = {note.title for note in notes}
    known_titles.update(alias for note in notes for alias in note.aliases)
    known_paths = {note.path for note in notes}

    links: list[LinkRecord] = []
    for path in md_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        body, _ = _strip_frontmatter(text)
        links.extend(_extract_links(path, vault_path, body, known_titles, known_paths))

    inbound = {link.target for link in links if link.resolved}
    outbound = {link.source for link in links}
    orphan_notes = sorted(note.title for note in notes if note.title not in inbound and note.title not in outbound)
    broken_links = [
        {"source": link.source, "target": link.target, "kind": link.kind, "raw": link.raw}
        for link in links
        if not link.resolved
    ]
    summary = {
        "notes": len(notes),
        "links": len(links),
        "wiki_links": sum(1 for link in links if link.kind == "wiki"),
        "markdown_links": sum(1 for link in links if link.kind == "markdown"),
        "broken_links": len(broken_links),
        "orphan_notes": len(orphan_notes),
    }
    result = VaultIndexResult(
        vault=str(vault_path),
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        notes=notes,
        links=links,
        orphan_notes=orphan_notes,
        broken_links=broken_links,
    )

    if output_db:
        _write_sqlite(Path(output_db), result)
    if output_json:
        out = Path(output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def render_markdown_report(result: VaultIndexResult) -> str:
    """Render a concise operator-facing vault health report."""

    lines = [
        "# Vault Health Report",
        "",
        f"Generated: `{result.generated_at}`",
        f"Vault: `{result.vault}`",
        "",
        "## Summary",
        "",
        f"- Notes: {result.summary['notes']}",
        f"- Links: {result.summary['links']}",
        f"- Wiki links: {result.summary['wiki_links']}",
        f"- Markdown links: {result.summary['markdown_links']}",
        f"- Broken links: {result.summary['broken_links']}",
        f"- Orphan notes: {result.summary['orphan_notes']}",
        "",
        "## Broken Links",
        "",
    ]
    if result.broken_links:
        for item in result.broken_links[:50]:
            lines.append(f"- `{item['source']}` → `{item['target']}` ({item['kind']})")
    else:
        lines.append("- None")

    lines.extend(["", "## Orphan Notes", ""])
    if result.orphan_notes:
        for title in result.orphan_notes[:50]:
            lines.append(f"- `{title}`")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Index a Markdown/Obsidian vault and report link health.")
    parser.add_argument("vault", type=Path, help="Path to the Markdown vault")
    parser.add_argument("--db", type=Path, default=None, help="Optional SQLite index output path")
    parser.add_argument("--json", type=Path, default=None, help="Optional JSON report output path")
    parser.add_argument("--markdown", type=Path, default=None, help="Optional Markdown report output path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = build_vault_index(args.vault, output_db=args.db, output_json=args.json)
    report = render_markdown_report(result)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
