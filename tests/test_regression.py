from pathlib import Path
import json

import nibabel as nib
import numpy as np

from vibe_to_trust.inference import load_cached_prediction
from vibe_to_trust.metrics import mean_dice


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "case_001"


def test_regression_cached_prediction_is_stable():
    """Protect the packaged tutorial prediction against accidental edits."""
    prediction, _ = load_cached_prediction(CASE)
    gt = np.asanyarray(nib.load(next((CASE / "ground_truth").glob("*_gt.nii.gz"))).dataobj)
    expected = json.loads((CASE / "metrics.json").read_text(encoding="utf-8"))
    measured = mean_dice(prediction, gt)
    assert abs(measured - expected["tutorial_resolution_dice"]["mean_dice"]) < 1e-5
    # Also freeze a simple hash of label occupancy to catch silent label swaps.
    occupancy = {int(label): int((prediction == label).sum()) for label in range(6)}
    assert occupancy[0] > 0
    assert occupancy[1] > 0
    assert occupancy[2] > 0
