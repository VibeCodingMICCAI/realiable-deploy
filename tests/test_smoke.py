from pathlib import Path
import json

import nibabel as nib
import numpy as np

from vibe_to_trust.inference import run_cached_pipeline
from vibe_to_trust.metrics import mean_dice
from vibe_to_trust.preprocessing import load_mri, validate_segmentation


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "case_001"


def test_smoke_cached_pipeline(tmp_path: Path):
    result = run_cached_pipeline(CASE, tmp_path)
    assert Path(result["output"]).is_file()
    assert result["mode"] == "cached"
    assert result["shape"] == [64, 64, 64]
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    validate_segmentation(pred)


def test_integration_pipeline_matches_ground_truth_dice(tmp_path: Path):
    result = run_cached_pipeline(CASE, tmp_path)
    image, _ = load_mri(next((CASE / "input").glob("*_mri.nii.gz")))
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    gt = np.asanyarray(nib.load(next((CASE / "ground_truth").glob("*_gt.nii.gz"))).dataobj)
    assert image.shape == pred.shape == gt.shape
    expected = json.loads((CASE / "metrics.json").read_text(encoding="utf-8"))
    measured = mean_dice(pred, gt)
    assert abs(measured - expected["tutorial_resolution_dice"]["mean_dice"]) < 1e-5
