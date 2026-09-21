"""Tests for stale-reuse teaching challenge and affine (optional advanced)."""

from pathlib import Path
import json

from vibe_to_trust.challenges.stale_reuse import (
    process_case,
    run_sequential,
    run_stale_regression_corrected,
    run_stale_regression_faulty,
    run_stale_weak,
    _derive_cases,
)
from vibe_to_trust.inference import EXAMPLE_CASE, run_cached_pipeline
from vibe_to_trust.metrics import mean_dice
from vibe_to_trust.nifti_io import load_segmentation_nifti


def test_weak_suite_passes_on_faulty(tmp_path: Path):
    result = run_stale_weak(tmp_path)
    assert result["ok"] is True


def test_sequential_faulty_returns_stale_for_B(tmp_path: Path):
    result = run_sequential(tmp_path, reuse_existing=True)
    assert result["meta"]["result_b"]["reused_existing"] is True
    assert result["meta"]["B_matches_B_reference"] is False
    assert result["meta"]["B_looks_like_A"] is True


def test_sequential_corrected_matches_B(tmp_path: Path):
    result = run_sequential(tmp_path, reuse_existing=False)
    assert result["meta"]["result_b"]["reused_existing"] is False
    assert result["meta"]["B_matches_B_reference"] is True


def test_regression_faulty_fails_expected(tmp_path: Path):
    result = run_stale_regression_faulty(tmp_path)
    assert result["ok"] is False
    assert result.get("expected_failure") is True


def test_regression_corrected_passes(tmp_path: Path):
    result = run_stale_regression_corrected(tmp_path)
    assert result["ok"] is True


def test_oracle_not_from_faulty(tmp_path: Path):
    cases = _derive_cases(tmp_path / "cases")
    ref_a, _ = load_segmentation_nifti(cases["A"]["ref_path"])
    ref_b, _ = load_segmentation_nifti(cases["B"]["ref_path"])
    assert mean_dice(ref_a, ref_b) < 0.99  # references differ


def test_packaged_case_untouched(tmp_path: Path):
    before = (EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8")
    run_stale_regression_faulty(tmp_path)
    run_cached_pipeline(EXAMPLE_CASE, tmp_path / "demo")
    after = (EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8")
    assert before == after
    json.loads(after)


def test_process_always_overwrite(tmp_path: Path):
    cases = _derive_cases(tmp_path / "cases")
    out = tmp_path / "out"
    process_case(cases["A"]["case_dir"], out, reuse_existing=False)
    r2 = process_case(cases["B"]["case_dir"], out, reuse_existing=False)
    assert r2["reused_existing"] is False
    pred, _ = load_segmentation_nifti(r2["output"])
    ref, _ = load_segmentation_nifti(cases["B"]["ref_path"])
    assert abs(mean_dice(pred, ref) - 1.0) < 1e-9
