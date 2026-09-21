"""Curated example B — geometry-aware test. Not collected by pytest as a second suite."""

import nibabel as nib
from vibe_to_trust.challenges.fixtures import write_synthetic_case
from vibe_to_trust.nifti_io import affines_match, load_segmentation_nifti


def test_saved_affine_matches_input(tmp_path):
    case = write_synthetic_case(tmp_path / "faulty", faulty_affine=True)
    mri = nib.load(case["mri_path"])
    _pred, aff = load_segmentation_nifti(case["pred_path"])
    assert affines_match(mri.affine, aff, rtol=0, atol=1e-5)
