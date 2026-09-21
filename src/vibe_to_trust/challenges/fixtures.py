"""Synthetic teaching fixtures (not clinical data)."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from vibe_to_trust.nifti_io import save_segmentation_nifti


# Non-identity affine: anisotropic spacing + translation.
TEACHING_AFFINE = np.array(
    [
        [0.7, 0.0, 0.0, 12.0],
        [0.0, 0.8, 0.0, -4.5],
        [0.0, 0.0, 1.2, 3.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
    dtype=float,
)


def make_synthetic_volume(shape: tuple[int, int, int] = (16, 16, 12)) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(mri, segmentation, affine)`` — synthetic teaching data only."""
    rng = np.random.default_rng(0)
    mri = rng.normal(loc=40.0, scale=12.0, size=shape).astype(np.float32)
    # Guarantee intensity variation for load_mri contracts.
    mri[0, 0, 0] = 0.0
    mri[-1, -1, -1] = 100.0

    seg = np.zeros(shape, dtype=np.uint8)
    seg[2:10, 2:10, 2:8] = 1  # Femur-like
    seg[3:9, 3:9, 4:7] = 2  # Cartilage-like
    seg[8:14, 2:10, 2:8] = 3  # Tibia-like
    seg[9:13, 3:7, 3:6] = 4
    seg[9:13, 7:11, 3:6] = 5
    return mri, seg, TEACHING_AFFINE.copy()


def write_synthetic_case(case_dir: Path, *, faulty_affine: bool = False) -> dict:
    """Write a tiny synthetic case under ``case_dir`` and return paths/metadata."""
    case_dir = Path(case_dir)
    input_dir = case_dir / "input"
    gt_dir = case_dir / "ground_truth"
    pred_dir = case_dir / "prediction"
    for folder in (input_dir, gt_dir, pred_dir):
        folder.mkdir(parents=True, exist_ok=True)

    mri, seg, affine = make_synthetic_volume()
    mri_path = input_dir / "synth_mri.nii.gz"
    gt_path = gt_dir / "synth_gt.nii.gz"
    pred_path = pred_dir / "synth_pred.nii.gz"

    nib.save(nib.Nifti1Image(mri, affine), mri_path)
    nib.save(nib.Nifti1Image(seg, affine), gt_path)
    save_segmentation_nifti(seg, affine, pred_path, use_identity_affine=faulty_affine)

    return {
        "case_dir": str(case_dir),
        "mri_path": str(mri_path),
        "gt_path": str(gt_path),
        "pred_path": str(pred_path),
        "affine": affine.tolist(),
        "shape": list(mri.shape),
        "faulty_affine": faulty_affine,
        "note": "Synthetic teaching data — not clinical imaging.",
    }
