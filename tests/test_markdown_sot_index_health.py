from pathlib import Path

from scripts.markdown_sot_index_health import audit_markdown_sot


def test_audit_detects_missing_fields_and_active_conflict(tmp_path: Path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "new.md").write_text(
        "---\nid: new\nstatus: active\nclients: [hermes]\nsupersedes: [old]\ncognitive_type: fact\n---\nnew\n",
        encoding="utf-8",
    )
    (vault / "old.md").write_text(
        "---\nid: old\nstatus: active\nclients: [hermes]\n---\nold\n",
        encoding="utf-8",
    )
    (vault / "plain.md").write_text("# plain note\nno protocol\n", encoding="utf-8")

    result = audit_markdown_sot(vault)
    codes = {f["code"] for f in result["findings"]}
    assert "active_supersedes_active" in codes
    assert "missing_protocol_fields" in codes
    assert result["ok"] is False
    assert result["protocol_note_count"] == 2


def test_healthy_protocol_notes_pass(tmp_path: Path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "a.md").write_text(
        "---\nid: a\nstatus: active\nclients: [hermes]\nsupersedes: []\ncognitive_type: preference\n---\nA\n",
        encoding="utf-8",
    )
    (vault / "b.md").write_text(
        "---\nid: b\nstatus: superseded\nclients: [hermes]\nsupersedes: []\ncognitive_type: preference\n---\nB\n",
        encoding="utf-8",
    )
    result = audit_markdown_sot(vault)
    assert result["ok"] is True
    assert result["summary"]["active_conflicts"] == 0
