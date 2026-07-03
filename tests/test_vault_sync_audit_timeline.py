from scripts.vault_sync_audit_timeline import normalize_flow_entries, timeline_to_jsonable


def test_normalize_flow_entries_sorts_and_preserves_reason():
    events = normalize_flow_entries({
        "id": "A",
        "flow_log": [
            {"timestamp": "2026-01-02T00:00:00Z", "source": "running", "target": "verification", "actor": "bot", "reason": "done"},
            {"timestamp": "2026-01-01T00:00:00Z", "source": "queued", "target": "running", "actor": "bot", "reason": "start"},
        ],
    })
    assert [e.summary for e in events] == ["queued -> running: start", "running -> verification: done"]
    assert timeline_to_jsonable(events)[0]["item_id"] == "A"
