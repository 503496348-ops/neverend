import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from real_sync_harness import compare_snapshots, run_reconnect_acceptance, snapshot_vault


def test_snapshot_detects_changed_note(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("alpha", encoding="utf-8")
    before = snapshot_vault(tmp_path)
    note.write_text("beta", encoding="utf-8")
    after = snapshot_vault(tmp_path)
    assert compare_snapshots(before, after)["changed"] == ["note.md"]


def _write_sync_fixture(path: Path) -> None:
    path.write_text(
        """from pathlib import Path
import shutil
import sys

mode = sys.argv[1]
if mode == "sync":
    source, replica = Path(sys.argv[2]), Path(sys.argv[3])
    source_files = {p.relative_to(source) for p in source.rglob("*.md")}
    for target in replica.rglob("*.md"):
        if target.relative_to(replica) not in source_files:
            target.unlink()
    for item in source.rglob("*.md"):
        target = replica / item.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
elif mode in {"fault", "restart"}:
    Path(sys.argv[2]).write_text(mode, encoding="utf-8")
""",
        encoding="utf-8",
    )


def test_reconnect_acceptance_drives_real_commands_and_cleans_probe(tmp_path):
    source = tmp_path / "source"
    replica = tmp_path / "replica"
    helper = tmp_path / "sync_fixture.py"
    marker = tmp_path / "transport-state"
    _write_sync_fixture(helper)

    result = run_reconnect_acceptance(
        source,
        replica,
        [sys.executable, str(helper), "sync", "{source}", "{replica}"],
        [sys.executable, str(helper), "fault", str(marker)],
        [sys.executable, str(helper), "restart", str(marker)],
        timeout=2,
        poll_interval=0.01,
    )

    assert result["passed"] is True
    assert result["checks"] == {
        "initial_replication": True,
        "fault_injected": True,
        "transport_restarted": True,
        "post_restart_replication": True,
        "cleanup_propagated": True,
    }
    assert [event["phase"] for event in result["events"]] == [
        "initial_sync",
        "inject_fault",
        "restart_transport",
        "post_restart_sync",
        "cleanup_sync",
    ]
    assert marker.read_text(encoding="utf-8") == "restart"
    assert not list(source.rglob("probe-*.md"))
    assert not list(replica.rglob("probe-*.md"))


def test_reconnect_acceptance_fails_when_replica_never_receives_probe(tmp_path):
    result = run_reconnect_acceptance(
        tmp_path / "source",
        tmp_path / "replica",
        [sys.executable, "-c", "pass"],
        [sys.executable, "-c", "pass"],
        [sys.executable, "-c", "pass"],
        timeout=0.02,
        poll_interval=0.005,
    )

    assert result["passed"] is False
    assert result["checks"]["initial_replication"] is False
    assert result["checks"]["post_restart_replication"] is False
