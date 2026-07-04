from pathlib import Path
from scripts.obsidian_sync_acceptance import compare_snapshots, detect_sync_conflicts, evaluate_sync_acceptance, snapshot_vault


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_snapshot_and_acceptance_pass_for_equal_vaults(tmp_path):
    source = tmp_path / "source"
    replica = tmp_path / "replica"
    write(source / "A.md", "# A\n[[B]]")
    write(replica / "A.md", "# A\n[[B]]")
    result = evaluate_sync_acceptance(source, replica)
    assert result["passed"] is True
    assert result["source_files"] == 1


def test_compare_snapshots_reports_changed_added_removed(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"
    write(a / "same.md", "x"); write(b / "same.md", "x")
    write(a / "changed.md", "old"); write(b / "changed.md", "new")
    write(a / "removed.md", "gone"); write(b / "added.md", "new")
    diff = compare_snapshots(snapshot_vault(a), snapshot_vault(b))
    assert diff["changed"] == ["changed.md"]
    assert diff["added"] == ["added.md"]
    assert diff["removed"] == ["removed.md"]


def test_conflict_detection_uses_filename_and_content_markers(tmp_path):
    write(tmp_path / "note sync-conflict.md", "text")
    write(tmp_path / "nested" / "merge.md", "<<<<<<< ours\n=======\n>>>>>>> theirs")
    reasons = {item["reason"] for item in detect_sync_conflicts(tmp_path)}
    assert reasons == {"conflict_marker_in_filename", "merge_marker_in_content"}
