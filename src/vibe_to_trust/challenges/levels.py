"""Level 1–3 optional challenge runners."""

from __future__ import annotations

from pathlib import Path
import tempfile
import uuid

import numpy as np

from vibe_to_trust.metrics import dice_score, mean_dice
from vibe_to_trust.nifti_io import affines_match, load_segmentation_nifti, save_segmentation_nifti
from vibe_to_trust.preprocessing import InputError, load_mri
from vibe_to_trust.provenance import array_sha256, collect_provenance

from .results import check, bundle
from .fixtures import write_synthetic_case


def _work(name: str, work_root: Path | None = None) -> Path:
    root = Path(work_root) if work_root is not None else Path(tempfile.gettempdir()) / "vibe_challenges"
    path = root / f"{name}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_level1_dice(work_root: Path | None = None) -> dict:
    """Independently calculable Dice: identical, disjoint, partial."""
    a = np.zeros((4, 4, 4), dtype=np.uint8)
    a[1:3, 1:3, 1:3] = 1  # 8 voxels
    identical = a.copy()
    disjoint = np.zeros_like(a)
    disjoint[0, 0, :] = 1  # no overlap with [1:3,1:3,1:3]
    partial = a.copy()
    partial[1, 1, 1] = 0  # 7 of 8 voxels remain → Dice = 2*7/(7+8) = 14/15

    d_id = dice_score(identical, a, 1)
    d_dis = dice_score(disjoint, a, 1)
    d_part = dice_score(partial, a, 1)
    # Empty-mask convention (this repo): both empty → 1.0
    d_empty = dice_score(np.zeros_like(a), np.zeros_like(a), 2)

    checks = [
        check("identical", abs(d_id - 1.0) < 1e-9, expected=1.0, observed=round(d_id, 6)),
        check("disjoint", abs(d_dis - 0.0) < 1e-9, expected=0.0, observed=round(d_dis, 6)),
        check(
            "partial_overlap",
            abs(d_part - (14 / 15)) < 1e-9,
            expected=round(14 / 15, 6),
            observed=round(d_part, 6),
            detail="One voxel removed from an 8-voxel cube → Dice=14/15",
        ),
        check(
            "both_empty_label",
            abs(d_empty - 1.0) < 1e-9,
            expected=1.0,
            observed=round(d_empty, 6),
            detail=(
                "Convention in this repo: if pred and ref are both empty for a label, Dice=1.0. "
                "Other projects use NaN or skip the label — state the convention when aggregating."
            ),
        ),
    ]
    return bundle(
        challenge_id="level1_dice",
        title="Level 1 · Dice contracts",
        command="challenge:level1_dice",
        checks=checks,
        explanation=(
            "Dice examples are deterministic array checks. "
            "Empty-mask convention here is Dice=1.0 when both masks are empty; "
            "that choice inflates mean Dice if many labels are absent."
        ),
        meta={"work_root": str(_work("dice", work_root))},
    )


def run_level1_shapes(work_root: Path | None = None) -> dict:
    """Mismatched shapes must not silently broadcast for mean_dice callers — we require equal shapes."""
    a = np.zeros((4, 4, 4), dtype=np.uint8)
    b = np.zeros((4, 4, 5), dtype=np.uint8)
    raised = False
    detail = "no error"
    try:
        if a.shape != b.shape:
            raise InputError(f"shape mismatch: {a.shape} vs {b.shape}")
        mean_dice(a, b)
    except InputError as exc:
        raised = True
        detail = str(exc)
    checks = [
        check(
            "reject_shape_mismatch",
            raised,
            expected="InputError / explicit reject",
            observed=detail,
            detail="Do not rely on NumPy broadcasting across volumes.",
        )
    ]
    return bundle(
        challenge_id="level1_shapes",
        title="Level 1 · Shape mismatch",
        command="challenge:level1_shapes",
        checks=checks,
        explanation="A correct contract rejects mismatched shapes instead of broadcasting.",
    )


def run_level1_invalid(work_root: Path | None = None) -> dict:
    work = _work("invalid", work_root)
    missing = work / "missing.nii.gz"
    raised_missing = False
    msg_missing = ""
    try:
        load_mri(missing)
    except InputError as exc:
        raised_missing = True
        msg_missing = str(exc)

    import nibabel as nib

    bad = work / "const.nii.gz"
    nib.save(nib.Nifti1Image(np.ones((6, 6, 6), dtype=np.float32), np.eye(4)), bad)
    raised_const = False
    msg_const = ""
    try:
        load_mri(bad)
    except InputError as exc:
        raised_const = True
        msg_const = str(exc)

    checks = [
        check("missing_file", raised_missing, expected="InputError", observed=msg_missing),
        check("constant_image", raised_const, expected="InputError", observed=msg_const),
    ]
    return bundle(
        challenge_id="level1_invalid",
        title="Level 1 · Invalid inputs",
        command="challenge:level1_invalid",
        checks=checks,
        explanation="Invalid inputs should fail with understandable InputError messages.",
    )


def run_level2_geometry(work_root: Path | None = None) -> dict:
    from .affine import run_affine_challenge

    # Geometry on faulty should fail (detect defect)
    faulty = run_affine_challenge(variant="faulty", suite="geometry", work_root=work_root)
    corrected = run_affine_challenge(variant="corrected", suite="geometry", work_root=work_root)
    checks = [
        check(
            "faulty_detected",
            not faulty["ok"],
            expected="geometry check fails on faulty",
            observed="failed" if not faulty["ok"] else "unexpectedly passed",
        ),
        check(
            "corrected_passes",
            corrected["ok"],
            expected="geometry check passes on corrected",
            observed="passed" if corrected["ok"] else "failed",
        ),
    ]
    return bundle(
        challenge_id="level2_geometry",
        title="Level 2 · Saved spatial geometry",
        command="challenge:level2_geometry",
        checks=checks,
        explanation="Integration: save then reload must preserve affine. Faulty identity-affine save is detected.",
        meta={"faulty": faulty["meta"], "corrected": corrected["meta"]},
    )


def run_level2_per_label(work_root: Path | None = None) -> dict:
    """Same mean Dice can hide a large per-label change."""
    gt = np.zeros((8, 8, 8), dtype=np.uint8)
    for label, sl in enumerate(
        [(1, 3, 1, 3, 1, 3), (3, 5, 1, 3, 1, 3), (5, 7, 1, 3, 1, 3), (1, 3, 3, 5, 1, 3), (3, 5, 3, 5, 1, 3)],
        start=1,
    ):
        x0, x1, y0, y1, z0, z1 = sl
        gt[x0:x1, y0:y1, z0:z1] = label

    pred_a = gt.copy()
    pred_b = gt.copy()
    # Destroy most of label 5 in B, boost others to keep mean similar is hard —
    # instead show identical mean with different per-label profile:
    # A: all labels perfect → mean 1.0
    # B: labels 1-4 perfect, label 5 empty vs gt nonempty → dice_5=0, mean=0.8
    pred_b[pred_b == 5] = 0

    mean_a = mean_dice(pred_a, gt)
    mean_b = mean_dice(pred_b, gt)
    d5_a = dice_score(pred_a, gt, 5)
    d5_b = dice_score(pred_b, gt, 5)

    checks = [
        check("mean_a", abs(mean_a - 1.0) < 1e-9, expected=1.0, observed=round(mean_a, 6)),
        check(
            "mean_hides_label5",
            abs(mean_b - 0.8) < 1e-9 and abs(d5_b - 0.0) < 1e-9,
            expected="mean≈0.8 with label5 Dice=0",
            observed={"mean": round(mean_b, 6), "label5": round(d5_b, 6), "label5_A": round(d5_a, 6)},
            detail="Aggregate mean Dice alone can miss a clinically important structure.",
        ),
    ]
    return bundle(
        challenge_id="level2_per_label",
        title="Level 2 · Mean Dice can hide per-label change",
        command="challenge:level2_per_label",
        checks=checks,
        explanation="Always inspect per-label metrics when structures matter unequally.",
    )


def run_level3_evidence(work_root: Path | None = None) -> dict:
    work = _work("evidence", work_root)
    case = work / "case"
    write_synthetic_case(case, faulty_affine=False)
    mri_path = Path(next((case / "input").glob("*_mri.nii.gz")))
    pred_path = Path(next((case / "prediction").glob("*_pred.nii.gz")))
    gt_path = Path(next((case / "ground_truth").glob("*_gt.nii.gz")))

    pred, pred_aff = load_segmentation_nifti(pred_path)
    gt = np.asanyarray(__import__("nibabel").load(str(gt_path)).dataobj)
    mri_aff = np.asarray(__import__("nibabel").load(str(mri_path)).affine, dtype=float)

    # Byte equality of two saves of the same array+affine
    p1 = work / "a.nii.gz"
    p2 = work / "b.nii.gz"
    save_segmentation_nifti(pred, pred_aff, p1)
    save_segmentation_nifti(pred, pred_aff, p2)
    same_bytes = p1.read_bytes() == p2.read_bytes()
    same_array = array_sha256(pred) == array_sha256(
        load_segmentation_nifti(p2)[0]
    )
    geom_ok = affines_match(mri_aff, pred_aff)
    per_label = {str(i): round(dice_score(pred, gt, i), 6) for i in range(1, 6)}
    record = collect_provenance(
        case_id="synthetic_teaching",
        input_path=mri_path,
        output_path=pred_path,
        output_array=pred,
        config={"mode": "synthetic_cached_path"},
    )

    checks = [
        check("arrays_match", same_array, expected=True, observed=same_array),
        check("geometry_match", geom_ok, expected=True, observed=geom_ok),
        check(
            "file_bytes_vs_semantic",
            True,
            expected="document difference",
            observed={"same_file_bytes": same_bytes, "same_array_hash": same_array},
            detail=(
                "File-byte equality can fail across compressors/timestamps even when "
                "arrays and affines are semantically equal. Prefer array/geometry/metric checks."
            ),
        ),
        check(
            "provenance_fields",
            all(k in record for k in ("tool_version", "input_sha256", "output_array_sha256")),
            expected="tool_version, input_sha256, output_array_sha256",
            observed=sorted(record.keys()),
        ),
    ]
    return bundle(
        challenge_id="level3_evidence",
        title="Level 3 · Reproducibility evidence",
        command="challenge:level3_evidence",
        checks=checks,
        explanation=(
            "Reproducing a cached synthetic result verifies the software path, not clinical performance. "
            "Byte-identical files are a stricter (and often brittle) requirement than semantic equivalence."
        ),
        meta={"per_label_dice": per_label, "provenance_keys": sorted(record.keys())},
    )


RUNNERS = None  # see challenges.runner
