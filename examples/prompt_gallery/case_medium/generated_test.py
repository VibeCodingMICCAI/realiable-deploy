"""Illustrative medium AI-generated test — NOT collected by pytest."""

from pathlib import Path

from vibe_to_trust.inference import run_cached_pipeline


def test_pipeline_runs(tmp_path: Path):
    case = Path("examples/case_001")
    result = run_cached_pipeline(case, tmp_path)
    assert Path(result["output"]).is_file()
    assert result["mode"] == "cached"
    # Missing: Dice vs metrics.json, invalid inputs, shape checks.
