import json
import sqlite3
from pathlib import Path

from scripts.vault_index import build_vault_index, render_markdown_report


def test_build_vault_index_detects_links_orphans_and_broken_links(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Inbox.md").write_text(
        "# Inbox\n\nLinks to [[Project Alpha]] and [missing](missing.md).\n",
        encoding="utf-8",
    )
    (vault / "Project Alpha.md").write_text(
        "# Project Alpha\n\nBacklink to [[Inbox]].\n",
        encoding="utf-8",
    )
    (vault / "Orphan.md").write_text("# Orphan\n\nNo links here.\n", encoding="utf-8")

    result = build_vault_index(vault, output_db=tmp_path / "index.sqlite", output_json=tmp_path / "report.json")

    assert result.summary["notes"] == 3
    assert result.summary["wiki_links"] == 2
    assert result.summary["markdown_links"] == 1
    assert result.summary["broken_links"] == 1
    assert "Orphan" in result.orphan_notes
    assert result.broken_links[0]["target"] == "missing.md"

    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["summary"]["notes"] == 3

    with sqlite3.connect(tmp_path / "index.sqlite") as conn:
        notes = conn.execute("select title from notes order by title").fetchall()
        links = conn.execute("select source, target, kind from links order by source, target").fetchall()
    assert notes == [("Inbox",), ("Orphan",), ("Project Alpha",)]
    assert ("Inbox", "Project Alpha", "wiki") in links


def test_render_markdown_report_contains_actionable_sections(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "A.md").write_text("[[Missing Note]]\n", encoding="utf-8")

    result = build_vault_index(vault)
    markdown = render_markdown_report(result)

    assert "# Vault Health Report" in markdown
    assert "## Broken Links" in markdown
    assert "Missing Note" in markdown
    assert "## Orphan Notes" in markdown
