"""Tests for the affine geometry teaching challenge (synthetic data only)."""

from pathlib import Path

from vibe_to_trust.challenges.affine import run_affine_challenge
from vibe_to_trust.challenges.runner import run_challenge


def test_weak_suite_passes_on_faulty_variant(tmp_path: Path):
    result = run_affine_challenge(variant="faulty", suite="weak", work_root=tmp_path)
    assert result["ok"] is True
    assert result["meta"]["affines_equal"] is False


def test_geometry_suite_fails_on_faulty_for_affine_reason(tmp_path: Path):
    result = run_affine_challenge(variant="faulty", suite="geometry", work_root=tmp_path)
    assert result["ok"] is False
    geom = result["checks"][0]
    assert geom["name"] == "saved_affine_matches_input"
    assert geom["pass"] is False


def test_geometry_suite_passes_on_corrected(tmp_path: Path):
    result = run_affine_challenge(variant="corrected", suite="geometry", work_root=tmp_path)
    assert result["ok"] is True
    assert result["meta"]["affines_equal"] is True


def test_packaged_case_untouched_by_challenge(tmp_path: Path):
    import json
    from vibe_to_trust.inference import EXAMPLE_CASE

    before = (EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8")
    run_affine_challenge(variant="faulty", suite="geometry", work_root=tmp_path)
    after = (EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8")
    assert before == after
    json.loads(after)  # still valid


def test_level_runners_smoke(tmp_path: Path):
    for cid in (
        "level1_dice",
        "level1_shapes",
        "level1_invalid",
        "level2_geometry",
        "level2_per_label",
        "level3_evidence",
    ):
        result = run_challenge(cid, work_root=tmp_path / cid)
        assert "checks" in result
        assert result["ok"] is True, cid
