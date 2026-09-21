from pathlib import Path
import json

import numpy as np
import pytest

from vibe_to_trust.metrics import dice_score, mean_dice
from vibe_to_trust.preprocessing import InputError, load_mri, validate_segmentation, zscore


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "case_001"


def test_load_mri_returns_expected_shape_and_dtype():
    path = next((CASE / "input").glob("*_mri.nii.gz"))
    data, affine = load_mri(path)
    assert data.ndim == 3
    assert data.shape == (64, 64, 64)
    assert data.dtype == np.float32
    assert affine.shape == (4, 4)


def test_zscore_unit_behaviour():
    data = np.arange(27, dtype=np.float32).reshape(3, 3, 3)
    normed = zscore(data)
    assert abs(float(normed.mean())) < 1e-5
    assert abs(float(normed.std()) - 1.0) < 1e-5


def test_validate_segmentation_labels():
    mask = np.zeros((4, 4, 4), dtype=np.uint8)
    mask[1:3, 1:3, 1:3] = 2
    out = validate_segmentation(mask)
    assert out.dtype == np.uint8
    assert set(np.unique(out)) <= {0, 1, 2, 3, 4, 5}
    bad = mask.astype(np.float32)
    bad[0, 0, 0] = 9
    with pytest.raises(InputError, match="unexpected"):
        validate_segmentation(bad)


def test_dice_known_example():
    pred = np.zeros((4, 4, 4), dtype=np.uint8)
    ref = np.zeros_like(pred)
    pred[1:3, 1:3, 1:3] = 1
    ref[1:3, 1:3, 1:3] = 1
    assert dice_score(pred, ref, 1) == 1.0
    ref[1, 1, 1] = 0
    score = dice_score(pred, ref, 1)
    assert 0.8 < score < 1.0


def test_missing_file_is_rejected(tmp_path: Path):
    with pytest.raises(InputError, match="does not exist"):
        load_mri(tmp_path / "missing.nii.gz")
