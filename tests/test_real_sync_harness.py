import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from real_sync_harness import compare_snapshots, snapshot_vault


def test_snapshot_detects_changed_note(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("alpha", encoding="utf-8")
    before = snapshot_vault(tmp_path)
    note.write_text("beta", encoding="utf-8")
    after = snapshot_vault(tmp_path)
    assert compare_snapshots(before, after)["changed"] == ["note.md"]
