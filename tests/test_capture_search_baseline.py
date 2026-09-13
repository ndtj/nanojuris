from __future__ import annotations

from pathlib import Path

from tools.capture_search_baseline import capture


def test_capture_baseline_is_hash_only(tmp_path: Path) -> None:
    report = capture(tmp_path / "baseline.json")
    assert report["capture_mode"] == "immutable_head_reconstruction"
    assert report["pre_code_snapshot_available"] is True
    assert report["raw_payloads_persisted"] is False
    assert report["reference_files"]
    assert report["offline_fixture_manifest"]
