"""Curated example A — plausible test that misses affine defects. Not collected by pytest."""

import nibabel as nib
from vibe_to_trust.challenges.fixtures import write_synthetic_case
from vibe_to_trust.metrics import mean_dice


def test_export_regression(tmp_path):
    case = write_synthetic_case(tmp_path, faulty_affine=False)
    pred = nib.load(case["pred_path"])
    gt = nib.load(case["gt_path"])
    assert mean_dice(pred.get_fdata(), gt.get_fdata()) == 1.0
    assert pred.shape == gt.shape
