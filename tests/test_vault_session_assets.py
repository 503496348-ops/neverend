from scripts.vault_session_assets import BridgeSessionAsset, BridgeSessionAssetIndex, build_markdown_manifest


def test_bridge_session_asset_index_detects_stale_policy():
    index = BridgeSessionAssetIndex()
    asset = BridgeSessionAsset("oc:thread", "claude", "/repo", "fp-old", "logs/run.jsonl")
    aid = index.add(asset)
    assert len(aid) == 20
    assert index.stale_after_policy_change("oc:thread", "fp-new") == [asset]
    assert "logs/run.jsonl" in build_markdown_manifest([asset])
