"""Tests for stand teaching examples (mean Dice + overlay)."""

from pathlib import Path

from vibe_to_trust.challenges.stand_examples import (
    run_mean_dice_regression_corrected,
    run_mean_dice_regression_faulty,
    run_mean_dice_reveal,
    run_mean_dice_weak,
    run_overlay_regression_corrected,
    run_overlay_regression_faulty,
    run_overlay_reveal,
    run_overlay_weak,
)
from vibe_to_trust.inference import EXAMPLE_CASE


def test_mean_dice_weak_passes_on_missing_structure(tmp_path: Path):
    result = run_mean_dice_weak(tmp_path)
    assert result["ok"] is True
    assert result["meta"]["gate"]["per_label"]["5"] == 0.0


def test_mean_dice_reveal_flags_critical_label(tmp_path: Path):
    result = run_mean_dice_reveal(tmp_path)
    assert result["expected_failure"] is True
    assert result["ok"] is False
    names = {c["name"]: c for c in result["checks"]}
    assert names["critical_structure_present"]["pass"] is False


def test_mean_dice_regression_faulty_expected_failure(tmp_path: Path):
    result = run_mean_dice_regression_faulty(tmp_path)
    assert result["expected_failure"] is True
    assert result["ok"] is False


def test_mean_dice_regression_corrected_passes(tmp_path: Path):
    result = run_mean_dice_regression_corrected(tmp_path)
    assert result["ok"] is True


def test_overlay_weak_passes_when_unbound(tmp_path: Path):
    result = run_overlay_weak(tmp_path)
    assert result["ok"] is True
    assert result["meta"]["result"]["overlay_matches_expected"] is False


def test_overlay_reveal_and_regression(tmp_path: Path):
    reveal = run_overlay_reveal(tmp_path / "reveal")
    assert reveal["expected_failure"] is True
    faulty = run_overlay_regression_faulty(tmp_path / "faulty")
    assert faulty["expected_failure"] is True
    assert faulty["ok"] is False
    corrected = run_overlay_regression_corrected(tmp_path / "ok")
    assert corrected["ok"] is True


def test_packaged_case_untouched(tmp_path: Path):
    before = (EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8")
    run_mean_dice_regression_faulty(tmp_path / "a")
    run_overlay_regression_faulty(tmp_path / "b")
    after = (EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8")
    assert before == after
