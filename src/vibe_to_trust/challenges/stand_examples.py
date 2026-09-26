"""Stand teaching examples: mean Dice hide, and overlay/result mismatch.

Seeded defects for the facilitator workshop — not claims about the production
cached pipeline.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import nibabel as nib
import numpy as np

from vibe_to_trust.inference import EXAMPLE_CASE, ROOT
from vibe_to_trust.metrics import dice_score, mean_dice
from vibe_to_trust.preprocessing import load_mri, validate_segmentation

from .results import bundle, check


def _relpath(path: Path | str) -> str:
    """Repo-relative POSIX path for portable sample JSON / UI meta."""
    p = Path(path).resolve()
    try:
        return p.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


LABELS = (1, 2, 3, 4, 5)
LABEL_NAMES = {
    1: "Femur",
    2: "Femoral Cartilage",
    3: "Tibia",
    4: "Medial Tibial Cartilage",
    5: "Lateral Tibial Cartilage",
}
# Structure that the teaching defect silently drops.
CRITICAL_LABEL = 5


def _work(name: str, work_root: Path | None) -> Path:
    root = Path(work_root) if work_root else Path("outputs") / "lab" / "stand"
    path = root / f"{name}_{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_packaged() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load packaged MRI / prediction / GT without modifying examples/case_001."""
    mri_path = next((EXAMPLE_CASE / "input").glob("*_mri.nii.gz"))
    pred_path = next((EXAMPLE_CASE / "prediction").glob("*_pred.nii.gz"))
    gt_path = next((EXAMPLE_CASE / "ground_truth").glob("*_gt.nii.gz"))
    mri, affine = load_mri(mri_path)
    pred = validate_segmentation(np.asanyarray(nib.load(str(pred_path)).dataobj))
    gt = validate_segmentation(np.asanyarray(nib.load(str(gt_path)).dataobj))
    return mri, pred, gt, np.asarray(affine)


def _drop_critical_label(pred: np.ndarray) -> np.ndarray:
    out = np.array(pred, copy=True)
    out[out == CRITICAL_LABEL] = 0
    return out


def _per_label_scores(pred: np.ndarray, gt: np.ndarray) -> dict[str, float]:
    return {str(label): round(dice_score(pred, gt, label), 6) for label in LABELS}


def accept_by_mean_only(pred: np.ndarray, gt: np.ndarray, *, threshold: float = 0.70) -> dict:
    """Faulty quality gate: only the aggregate mean Dice is checked."""
    mean = mean_dice(pred, gt, LABELS)
    return {
        "accepted": mean >= threshold,
        "mean_dice": round(mean, 6),
        "per_label": _per_label_scores(pred, gt),
        "policy": "mean_only",
        "threshold": threshold,
    }


def accept_with_per_label(
    pred: np.ndarray,
    gt: np.ndarray,
    *,
    mean_threshold: float = 0.70,
    per_label_threshold: float = 0.5,
) -> dict:
    """Corrected quality gate: mean and each structure must clear a floor."""
    mean = mean_dice(pred, gt, LABELS)
    per_label = _per_label_scores(pred, gt)
    label_ok = all(v >= per_label_threshold for v in per_label.values())
    return {
        "accepted": mean >= mean_threshold and label_ok,
        "mean_dice": round(mean, 6),
        "per_label": per_label,
        "policy": "mean_and_per_label",
        "mean_threshold": mean_threshold,
        "per_label_threshold": per_label_threshold,
        "critical_label": CRITICAL_LABEL,
        "critical_name": LABEL_NAMES[CRITICAL_LABEL],
        "critical_dice": per_label[str(CRITICAL_LABEL)],
    }


def run_mean_dice_weak(work_root: Path | None = None) -> dict:
    """Initial checks that only look at mean Dice — pass on a missing structure."""
    _ = _work("mean_weak", work_root)
    _, pred_full, gt, _ = _load_packaged()
    pred_bad = _drop_critical_label(pred_full)
    gate = accept_by_mean_only(pred_bad, gt)

    checks = [
        check(
            "mean_dice_above_threshold",
            gate["accepted"],
            expected=f"mean_dice >= {gate['threshold']}",
            observed=gate["mean_dice"],
            detail="Vague checks often stop at an aggregate score.",
        ),
        check(
            "prediction_nonempty",
            int(np.count_nonzero(pred_bad)) > 0,
            expected=True,
            observed=True,
        ),
        check(
            "labels_look_plausible",
            set(int(v) for v in np.unique(pred_bad)) <= {0, *LABELS},
            expected="subset of {0..5}",
            observed=sorted(int(v) for v in np.unique(pred_bad)),
        ),
    ]
    return bundle(
        challenge_id="mean_dice_weak",
        title="Initial checks · mean Dice only",
        command="challenge:mean_dice_weak",
        checks=checks,
        explanation=(
            "These checks pass while Lateral Tibial Cartilage (label 5) is entirely missing. "
            "A high mean Dice does not prove every structure is present."
        ),
        meta={
            "gate": gate,
            "critical_label": CRITICAL_LABEL,
            "critical_name": LABEL_NAMES[CRITICAL_LABEL],
            "assets": {
                "full": "assets/teaching/mean_full.png",
                "missing_label5": "assets/teaching/mean_missing_label5.png",
            },
        },
    )


def run_mean_dice_reveal(work_root: Path | None = None) -> dict:
    """Show mean vs per-label numbers for the teaching prediction."""
    _ = _work("mean_reveal", work_root)
    _, pred_full, gt, _ = _load_packaged()
    pred_bad = _drop_critical_label(pred_full)
    full = accept_with_per_label(pred_full, gt)
    bad = accept_with_per_label(pred_bad, gt)
    checks = [
        check(
            "mean_still_looks_ok",
            bad["mean_dice"] >= 0.70,
            expected="mean_dice >= 0.70",
            observed=bad["mean_dice"],
        ),
        check(
            "critical_structure_present",
            bad["critical_dice"] >= 0.5,
            expected=f"{LABEL_NAMES[CRITICAL_LABEL]} Dice >= 0.5",
            observed=bad["critical_dice"],
            detail="Expected failure: label 5 was dropped in the teaching prediction.",
        ),
    ]
    result = bundle(
        challenge_id="mean_dice_reveal",
        title="Inspect mean vs per-label Dice",
        command="challenge:mean_dice_reveal",
        checks=checks,
        explanation=(
            f"Mean Dice ≈ {bad['mean_dice']} while {LABEL_NAMES[CRITICAL_LABEL]} Dice = "
            f"{bad['critical_dice']}. Aggregate metrics can hide a clinically important failure."
        ),
        meta={
            "full_prediction": full,
            "teaching_prediction": bad,
            "assets": {
                "full": "assets/teaching/mean_full.png",
                "missing_label5": "assets/teaching/mean_missing_label5.png",
            },
        },
    )
    result["expected_failure"] = True
    result["ok"] = False
    return result


def run_mean_dice_regression_faulty(work_root: Path | None = None) -> dict:
    """Stronger per-label test against the mean-only gate — expected failure."""
    _ = _work("mean_reg_faulty", work_root)
    _, pred_full, gt, _ = _load_packaged()
    pred_bad = _drop_critical_label(pred_full)
    weak = accept_by_mean_only(pred_bad, gt)
    strong = accept_with_per_label(pred_bad, gt)
    checks = [
        check(
            "mean_only_gate_accepts",
            weak["accepted"] is True,
            expected=True,
            observed=weak["accepted"],
            detail="Informative: the weak gate still accepts.",
        ),
        check(
            "per_label_gate_accepts",
            strong["accepted"] is True,
            expected=True,
            observed=False,
            detail=(
                f"Expected failure: {LABEL_NAMES[CRITICAL_LABEL]} Dice = "
                f"{strong['critical_dice']} under the teaching defect."
            ),
        ),
    ]
    result = bundle(
        challenge_id="mean_dice_regression_faulty",
        title="Stronger test · mean-only gate (faulty)",
        command="challenge:mean_dice_regression_faulty",
        checks=checks,
        explanation=(
            "A focused test that requires every structure to meet a Dice floor detects the defect. "
            "Treating that failure as successful defect detection."
        ),
        meta={"weak": weak, "strong": strong},
    )
    result["expected_failure"] = True
    result["ok"] = False
    result["message"] = (
        "Expected failure: per-label check detected a missing structure that mean Dice hid."
    )
    return result


def run_mean_dice_regression_corrected(work_root: Path | None = None) -> dict:
    """Same stronger test with a complete prediction and the per-label gate."""
    _ = _work("mean_reg_ok", work_root)
    _, pred_full, gt, _ = _load_packaged()
    strong = accept_with_per_label(pred_full, gt)
    checks = [
        check(
            "per_label_gate_accepts",
            strong["accepted"] is True,
            expected=True,
            observed=strong["accepted"],
            detail="Packaged prediction keeps all five structures.",
        ),
        check(
            "critical_structure_ok",
            strong["critical_dice"] >= 0.5,
            expected=f"{LABEL_NAMES[CRITICAL_LABEL]} Dice >= 0.5",
            observed=strong["critical_dice"],
        ),
    ]
    return bundle(
        challenge_id="mean_dice_regression_corrected",
        title="Stronger test · per-label gate (corrected)",
        command="challenge:mean_dice_regression_corrected",
        checks=checks,
        explanation=(
            "Minimal fix: require a per-label floor (and keep checking mean). "
            "Do not rely on mean Dice alone when structures matter unequally."
        ),
        meta={"strong": strong},
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_slice_overlay(
    image: np.ndarray,
    prediction: np.ndarray,
    output_path: Path,
    *,
    z: int,
) -> Path:
    """Write a single-panel overlay at a chosen axial index (teaching helper)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    z = int(np.clip(z, 0, image.shape[2] - 1))
    base = image[:, :, z]
    lo, hi = np.percentile(base, (1, 99))
    base = np.clip((base - lo) / (hi - lo + 1e-6), 0, 1)
    rgb = np.stack([base, base, base], axis=-1)
    colors = {
        1: (1.0, 0.2, 0.2),
        2: (1.0, 0.85, 0.1),
        3: (0.2, 0.55, 1.0),
        4: (0.2, 0.9, 0.4),
        5: (0.9, 0.3, 0.9),
    }
    overlay = rgb.copy()
    for label, color in colors.items():
        mask = prediction[:, :, z] == label
        for channel, value in enumerate(color):
            overlay[:, :, channel] = np.where(
                mask, 0.45 * overlay[:, :, channel] + 0.55 * value, overlay[:, :, channel]
            )
    fig, ax = plt.subplots(1, 1, figsize=(3.4, 3.4), dpi=120)
    ax.imshow(overlay.transpose(1, 0, 2), origin="lower")
    ax.set_title(f"overlay z={z}")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def export_case_outputs(
    out_dir: Path,
    *,
    bind_overlay_to_prediction: bool,
) -> dict:
    """Save prediction.nii.gz and overlay.png under a teaching bind policy."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mri, pred, gt, affine = _load_packaged()
    pred_path = out_dir / "prediction.nii.gz"
    overlay_path = out_dir / "overlay.png"
    nib.save(nib.Nifti1Image(pred.astype(np.uint8), affine), pred_path)

    mid_z = int(mri.shape[2] // 2)
    stale_z = 0
    if bind_overlay_to_prediction:
        _save_slice_overlay(mri, pred, overlay_path, z=mid_z)
        policy = "bind_current_prediction"
        overlay_z = mid_z
    else:
        # Faulty teaching policy: write an overlay from another slice than the
        # mid-slice used for inspection — looks like an overlay, wrong content.
        _save_slice_overlay(mri, pred, overlay_path, z=stale_z)
        policy = "stale_or_unbound_overlay"
        overlay_z = stale_z

    expected = out_dir / "expected_overlay.png"
    _save_slice_overlay(mri, pred, expected, z=mid_z)
    return {
        "ok": True,
        "prediction": _relpath(pred_path),
        "overlay": _relpath(overlay_path),
        "expected_overlay": _relpath(expected),
        "overlay_matches_expected": _sha256(overlay_path) == _sha256(expected),
        "policy": policy,
        "overlay_z": overlay_z,
        "expected_z": mid_z,
        "shape": list(pred.shape),
    }


def run_overlay_weak(work_root: Path | None = None) -> dict:
    """Initial checks: overlay exists — pass even when unbound from mid-slice."""
    work = _work("overlay_weak", work_root)
    result = export_case_outputs(work / "out", bind_overlay_to_prediction=False)
    overlay = Path(result["overlay"])
    checks = [
        check("overlay_exists", overlay.is_file(), expected=True, observed=overlay.is_file()),
        check(
            "overlay_is_png",
            overlay.suffix.lower() == ".png",
            expected=".png",
            observed=overlay.suffix.lower(),
        ),
        check(
            "overlay_nonempty",
            overlay.stat().st_size > 1000,
            expected="size > 1000 bytes",
            observed=overlay.stat().st_size,
        ),
    ]
    return bundle(
        challenge_id="overlay_weak",
        title="Initial checks · overlay file present",
        command="challenge:overlay_weak",
        checks=checks,
        explanation=(
            "File-existence checks pass while the PNG was written from the wrong axial slice. "
            "A valid-looking overlay is not proof it matches the saved segmentation view."
        ),
        meta={
            "result": result,
            "assets": {
                "bound": "assets/teaching/overlay_bound.png",
                "stale": "assets/teaching/overlay_stale.png",
            },
        },
    )


def run_overlay_reveal(work_root: Path | None = None) -> dict:
    """Compare bound vs unbound overlay for the same prediction."""
    work = _work("overlay_reveal", work_root)
    bad = export_case_outputs(work / "bad", bind_overlay_to_prediction=False)
    good = export_case_outputs(work / "good", bind_overlay_to_prediction=True)
    checks = [
        check(
            "prediction_saved",
            Path(bad["prediction"]).is_file(),
            expected=True,
            observed=True,
        ),
        check(
            "overlay_matches_current_mid_slice",
            bad["overlay_matches_expected"] is True,
            expected=True,
            observed=False,
            detail=(
                f"Expected failure: overlay used z={bad['overlay_z']}, "
                f"inspection mid-slice is z={bad['expected_z']}."
            ),
        ),
    ]
    result = bundle(
        challenge_id="overlay_reveal",
        title="Inspect overlay vs saved segmentation",
        command="challenge:overlay_reveal",
        checks=checks,
        explanation=(
            "The NIfTI prediction can be correct while overlay.png shows a different slice. "
            "Inspection images must be regenerated from the current prediction."
        ),
        meta={
            "faulty": bad,
            "corrected": good,
            "assets": {
                "bound": "assets/teaching/overlay_bound.png",
                "stale": "assets/teaching/overlay_stale.png",
            },
        },
    )
    result["expected_failure"] = True
    result["ok"] = False
    return result


def run_overlay_regression_faulty(work_root: Path | None = None) -> dict:
    work = _work("overlay_reg_faulty", work_root)
    result = export_case_outputs(work / "out", bind_overlay_to_prediction=False)
    checks = [
        check(
            "overlay_bound_to_current_prediction",
            result["overlay_matches_expected"] is True,
            expected=True,
            observed=False,
            detail="Expected failure: teaching policy wrote an unbound / wrong-slice overlay.",
        ),
    ]
    out = bundle(
        challenge_id="overlay_regression_faulty",
        title="Stronger test · unbound overlay (faulty)",
        command="challenge:overlay_regression_faulty",
        checks=checks,
        explanation=(
            "Regenerate the expected mid-slice overlay from the saved prediction and compare. "
            "Do not only assert that overlay.png exists."
        ),
        meta={"result": result},
    )
    out["expected_failure"] = True
    out["ok"] = False
    out["message"] = "Expected failure: overlay content does not match the current mid-slice prediction."
    return out


def run_overlay_regression_corrected(work_root: Path | None = None) -> dict:
    work = _work("overlay_reg_ok", work_root)
    result = export_case_outputs(work / "out", bind_overlay_to_prediction=True)
    checks = [
        check(
            "overlay_bound_to_current_prediction",
            result["overlay_matches_expected"] is True,
            expected=True,
            observed=True,
            detail="Overlay regenerated from the current prediction at the mid slice.",
        ),
    ]
    return bundle(
        challenge_id="overlay_regression_corrected",
        title="Stronger test · bound overlay (corrected)",
        command="challenge:overlay_regression_corrected",
        checks=checks,
        explanation=(
            "Minimal fix: always regenerate overlay.png from the current prediction "
            "(and the intended slice index) when exporting results."
        ),
        meta={"result": result},
    )


def export_teaching_assets(dest: Path) -> dict[str, str]:
    """Write PNG assets used by the stand (does not modify packaged references)."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    mri, pred, _, _ = _load_packaged()
    mid = int(mri.shape[2] // 2)
    paths = {
        "mean_full": dest / "mean_full.png",
        "mean_missing_label5": dest / "mean_missing_label5.png",
        "overlay_bound": dest / "overlay_bound.png",
        "overlay_stale": dest / "overlay_stale.png",
    }
    _save_slice_overlay(mri, pred, paths["mean_full"], z=mid)
    _save_slice_overlay(mri, _drop_critical_label(pred), paths["mean_missing_label5"], z=mid)
    _save_slice_overlay(mri, pred, paths["overlay_bound"], z=mid)
    _save_slice_overlay(mri, pred, paths["overlay_stale"], z=0)
    return {k: _relpath(v) for k, v in paths.items()}


def ensure_teaching_assets(website_dir: Path | None = None) -> Path:
    """Create teaching PNGs under website/assets/teaching if any are missing."""
    dest = Path(website_dir or (ROOT / "website")) / "assets" / "teaching"
    required = (
        "mean_full.png",
        "mean_missing_label5.png",
        "overlay_bound.png",
        "overlay_stale.png",
    )
    if all((dest / name).is_file() for name in required):
        return dest
    export_teaching_assets(dest)
    return dest
