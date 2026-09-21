"""Curated example C — wrong contract (expects identity). Not collected by pytest."""

from pathlib import Path
import nibabel as nib
import numpy as np
from vibe_to_trust.challenges.fixtures import write_synthetic_case


def test_export_looks_ok(tmp_path):
    case = write_synthetic_case(tmp_path, faulty_affine=True)
    pred = Path(case["pred_path"])
    assert pred.is_file()
    img = nib.load(pred)
    assert img.ndim == 3
    assert np.allclose(img.affine, np.eye(4))
