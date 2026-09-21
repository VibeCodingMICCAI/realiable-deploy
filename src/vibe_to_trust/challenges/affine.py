"""Core challenge: weak tests pass while saved spatial geometry is wrong."""

from __future__ import annotations

from pathlib import Path
import tempfile
import uuid

import nibabel as nib
import numpy as np

from vibe_to_trust.metrics import mean_dice
from vibe_to_trust.nifti_io import affines_match, load_segmentation_nifti
from vibe_to_trust.preprocessing import validate_segmentation

from .results import check, bundle
from .fixtures import write_synthetic_case


def _workdir(base: Path | None = None) -> Path:
    root = Path(base) if base is not None else Path(tempfile.gettempdir()) / "vibe_challenges"
    path = root / f"affine_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_weak_checks(case_dir: Path) -> list[dict]:
    """Initial suite: file, shape, labels, array Dice — does NOT check affine."""
    case_dir = Path(case_dir)
    mri_path = next((case_dir / "input").glob("*_mri.nii.gz"))
    gt_path = next((case_dir / "ground_truth").glob("*_gt.nii.gz"))
    pred_path = next((case_dir / "prediction").glob("*_pred.nii.gz"))

    mri_img = nib.load(str(mri_path))
    gt = np.asanyarray(nib.load(str(gt_path)).dataobj)
    pred = np.asanyarray(nib.load(str(pred_path)).dataobj)

    checks = []
    checks.append(check("output_exists", pred_path.is_file(), expected=True, observed=pred_path.is_file(), detail=str(pred_path)))
    checks.append(
        check(
            "shape_matches_mri",
            pred.shape == mri_img.shape,
            expected=list(mri_img.shape),
            observed=list(pred.shape),
        )
    )
    try:
        validate_segmentation(pred)
        checks.append(check("valid_labels", True, expected="labels in {0..5}", observed="ok"))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("valid_labels", False, expected="labels in {0..5}", observed=str(exc)))

    dice = mean_dice(pred, gt)
    checks.append(
        check(
            "array_dice_vs_gt",
            abs(dice - 1.0) < 1e-9,
            expected=1.0,
            observed=round(dice, 6),
            detail="Array Dice ignores NIfTI affine.",
        )
    )
    return checks


def run_geometry_check(case_dir: Path) -> list[dict]:
    """Stronger check: reload saved prediction and compare affine to input MRI."""
    case_dir = Path(case_dir)
    mri_path = next((case_dir / "input").glob("*_mri.nii.gz"))
    pred_path = next((case_dir / "prediction").glob("*_pred.nii.gz"))
    mri_affine = np.asarray(nib.load(str(mri_path)).affine, dtype=float)
    _pred, pred_affine = load_segmentation_nifti(pred_path)
    matched = affines_match(mri_affine, pred_affine, rtol=0.0, atol=1e-5)
    return [
        check(
            "saved_affine_matches_input",
            matched,
            expected=mri_affine.round(5).tolist(),
            observed=pred_affine.round(5).tolist(),
            detail="rtol=0, atol=1e-5 after NIfTI save/load",
        )
    ]


def run_affine_challenge(
    *,
    variant: str,
    suite: str,
    work_root: Path | None = None,
) -> dict:
    """Run weak or geometry suite on faulty or corrected synthetic variant.

    Parameters
    ----------
    variant:
        ``faulty`` saves correct arrays with an identity affine.
        ``corrected`` preserves the teaching affine.
    suite:
        ``weak`` or ``geometry``.
    """
    if variant not in {"faulty", "corrected"}:
        raise ValueError(f"unknown variant: {variant}")
    if suite not in {"weak", "geometry"}:
        raise ValueError(f"unknown suite: {suite}")

    work = _workdir(work_root)
    case_dir = work / "case"
    write_synthetic_case(case_dir, faulty_affine=(variant == "faulty"))

    if suite == "weak":
        checks = run_weak_checks(case_dir)
        title = f"Initial checks on {variant} variant"
        explanation = (
            "These checks exercise file existence, shape, labels, and array Dice. "
            "They do not reload and compare the saved NIfTI affine to the input."
        )
        command = f"challenge:affine suite=weak variant={variant}"
    else:
        checks = run_geometry_check(case_dir)
        title = f"Geometry check on {variant} variant"
        if variant == "faulty":
            explanation = (
                "Expected failure: the seeded defect writes an identity affine. "
                "A failing geometry check here means the test detected the defect — "
                "not an unexpected execution error."
            )
        else:
            explanation = (
                "Corrected save preserves the input affine through the NIfTI boundary. "
                "This is software verification on synthetic data, not model-performance validation."
            )
        command = f"challenge:affine suite=geometry variant={variant}"

    # Inspect geometry for the UI even on weak suite
    mri_path = next((case_dir / "input").glob("*_mri.nii.gz"))
    pred_path = next((case_dir / "prediction").glob("*_pred.nii.gz"))
    mri_aff = np.asarray(nib.load(str(mri_path)).affine, dtype=float)
    pred_aff = np.asarray(nib.load(str(pred_path)).affine, dtype=float)

    return bundle(
        challenge_id=f"affine_{suite}_{variant}",
        title=title,
        command=command,
        checks=checks,
        explanation=explanation,
        meta={
            "variant": variant,
            "suite": suite,
            "synthetic": True,
            "case_dir": str(case_dir),
            "input_affine": mri_aff.round(5).tolist(),
            "output_affine": pred_aff.round(5).tolist(),
            "affines_equal": affines_match(mri_aff, pred_aff),
        },
    )
