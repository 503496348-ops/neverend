"""Executable dual-vault sync and reconnect acceptance harness."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time
from typing import Sequence
import uuid


@dataclass(frozen=True)
class VaultProbe:
    relative_path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class CommandEvent:
    phase: str
    command: list[str]
    returncode: int | None
    passed: bool
    stdout: str = ""
    stderr: str = ""


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
    payload = [asdict(probe) for probe in probes]
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _expand_command(command: Sequence[str], source: Path, replica: Path) -> list[str]:
    return [
        part.replace("{source}", str(source)).replace("{replica}", str(replica))
        for part in command
    ]


def _run_command(
    phase: str,
    command: Sequence[str],
    source: Path,
    replica: Path,
    timeout: float,
) -> CommandEvent:
    expanded = _expand_command(command, source, replica)
    if not expanded:
        return CommandEvent(phase, [], None, False, stderr="command is empty")
    try:
        result = subprocess.run(
            expanded,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandEvent(phase, expanded, None, False, stderr=str(exc))
    return CommandEvent(
        phase=phase,
        command=expanded,
        returncode=result.returncode,
        passed=result.returncode == 0,
        stdout=result.stdout[-2000:],
        stderr=result.stderr[-2000:],
    )


def _wait_for_probe(source_probe: Path, replica_probe: Path, timeout: float, poll_interval: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        if source_probe.exists() and replica_probe.exists():
            if source_probe.read_bytes() == replica_probe.read_bytes():
                return True
        time.sleep(poll_interval)
    return False


def _wait_for_deletion(replica_probe: Path, timeout: float, poll_interval: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        if not replica_probe.exists():
            return True
        time.sleep(poll_interval)
    return False


def run_reconnect_acceptance(
    source: str | Path,
    replica: str | Path,
    sync_command: Sequence[str],
    fault_command: Sequence[str],
    restart_command: Sequence[str],
    *,
    timeout: float = 10.0,
    poll_interval: float = 0.1,
) -> dict[str, object]:
    """Exercise initial sync, transport failure, restart and post-restart sync.

    Commands execute without a shell. Each argument may contain ``{source}`` or
    ``{replica}`` placeholders. The sync command must be a bounded, one-shot
    operation; daemons should be controlled by the fault/restart commands.
    """
    source_root = Path(source).resolve()
    replica_root = Path(replica).resolve()
    source_root.mkdir(parents=True, exist_ok=True)
    replica_root.mkdir(parents=True, exist_ok=True)
    relative_probe = Path(".neverend-smoke") / f"probe-{uuid.uuid4().hex}.md"
    source_probe = source_root / relative_probe
    replica_probe = replica_root / relative_probe
    source_probe.parent.mkdir(parents=True, exist_ok=True)

    events: list[CommandEvent] = []
    checks: dict[str, bool] = {}
    cleanup_ok = False
    try:
        source_probe.write_text("phase=initial\n", encoding="utf-8")
        event = _run_command("initial_sync", sync_command, source_root, replica_root, timeout)
        events.append(event)
        checks["initial_replication"] = event.passed and _wait_for_probe(
            source_probe, replica_probe, timeout, poll_interval
        )

        event = _run_command("inject_fault", fault_command, source_root, replica_root, timeout)
        events.append(event)
        checks["fault_injected"] = event.passed

        source_probe.write_text("phase=after-restart\n", encoding="utf-8")
        event = _run_command("restart_transport", restart_command, source_root, replica_root, timeout)
        events.append(event)
        checks["transport_restarted"] = event.passed

        event = _run_command("post_restart_sync", sync_command, source_root, replica_root, timeout)
        events.append(event)
        checks["post_restart_replication"] = event.passed and _wait_for_probe(
            source_probe, replica_probe, timeout, poll_interval
        )
    finally:
        source_probe.unlink(missing_ok=True)
        event = _run_command("cleanup_sync", sync_command, source_root, replica_root, timeout)
        events.append(event)
        cleanup_ok = event.passed and _wait_for_deletion(replica_probe, timeout, poll_interval)
        checks["cleanup_propagated"] = cleanup_ok
        for parent in (source_probe.parent, replica_probe.parent):
            try:
                parent.rmdir()
            except OSError:
                pass

    passed = all(checks.values()) and all(event.passed for event in events)
    return {
        "passed": passed,
        "source": str(source_root),
        "replica": str(replica_root),
        "probe": relative_probe.as_posix(),
        "checks": checks,
        "events": [asdict(event) for event in events],
    }


def _parse_command(value: str) -> list[str]:
    command = shlex.split(value)
    if not command:
        raise argparse.ArgumentTypeError("command cannot be empty")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real dual-vault reconnect acceptance")
    parser.add_argument("source", help="source vault directory")
    parser.add_argument("replica", help="replica vault directory")
    parser.add_argument("--sync-command", required=True, type=_parse_command)
    parser.add_argument("--fault-command", required=True, type=_parse_command)
    parser.add_argument("--restart-command", required=True, type=_parse_command)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("--json-output", help="optional path for the JSON evidence report")
    args = parser.parse_args()
    result = run_reconnect_acceptance(
        args.source,
        args.replica,
        args.sync_command,
        args.fault_command,
        args.restart_command,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_output:
        Path(args.json_output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
