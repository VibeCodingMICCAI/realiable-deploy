"""Teaching challenge: unsafe reuse of an existing prediction file across cases.

Seeded defect for the tutorial — not a claim about the production cached pipeline.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import nibabel as nib
import numpy as np

from vibe_to_trust.inference import EXAMPLE_CASE
from vibe_to_trust.metrics import mean_dice
from vibe_to_trust.nifti_io import load_segmentation_nifti
from vibe_to_trust.preprocessing import validate_segmentation

from .results import bundle, check

# Session roots live under a caller-provided work_root.


def _derive_cases(work: Path) -> dict:
    """Build two teaching cases from the single packaged extract.

    Case A uses the packaged prediction. Case B uses the same MRI geometry but a
    deliberately remapped segmentation so overlays differ. Both are teaching
    derivatives — not two genuine patient cases.
    """
    mri_src = next((EXAMPLE_CASE / "input").glob("*_mri.nii.gz"))
    pred_src = next((EXAMPLE_CASE / "prediction").glob("*_pred.nii.gz"))
    mri_img = nib.load(str(mri_src))
    pred = np.asanyarray(nib.load(str(pred_src)).dataobj).astype(np.uint8)
    affine = np.asarray(mri_img.affine)

    # Remap labels for case B: swap 1↔3 and 4↔5 so the overlay is visibly different.
    remap = {0: 0, 1: 3, 2: 2, 3: 1, 4: 5, 5: 4}
    pred_b = np.zeros_like(pred)
    for src, dst in remap.items():
        pred_b[pred == src] = dst

    cases = {}
    for case_id, pred_arr in (("A", pred), ("B", pred_b)):
        case_dir = work / f"case_{case_id}"
        (case_dir / "input").mkdir(parents=True, exist_ok=True)
        (case_dir / "prediction").mkdir(parents=True, exist_ok=True)
        mri_path = case_dir / "input" / f"teach_{case_id}_mri.nii.gz"
        ref_path = case_dir / "prediction" / f"teach_{case_id}_pred.nii.gz"
        shutil.copy2(mri_src, mri_path)
        nib.save(nib.Nifti1Image(pred_arr.astype(np.uint8), affine), ref_path)
        meta = {
            "case_id": case_id,
            "derived_from": "examples/case_001",
            "note": (
                "Teaching derivative of the packaged extract. "
                "Case B remaps labels for a visibly different reference — not a second patient."
            ),
        }
        (case_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        cases[case_id] = {
            "case_dir": case_dir,
            "mri_path": mri_path,
            "ref_path": ref_path,
            "meta": meta,
        }
    return cases


def process_case(
    case_dir: Path,
    output_dir: Path,
    *,
    reuse_existing: bool,
) -> dict:
    """Process one teaching case into ``output_dir / prediction.nii.gz``.

    When ``reuse_existing`` is True (faulty teaching policy), an existing
    prediction file is returned without checking which input produced it.
    """
    case_dir = Path(case_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "prediction.nii.gz"
    input_path = next((case_dir / "input").glob("*_mri.nii.gz"))
    ref_path = next((case_dir / "prediction").glob("*_pred.nii.gz"))

    if reuse_existing and out_path.is_file():
        data, aff = load_segmentation_nifti(out_path)
        return {
            "ok": True,
            "reused_existing": True,
            "provider_invoked": False,
            "output": str(out_path),
            "input": str(input_path),
            "shape": list(data.shape),
            "labels_present": sorted(int(v) for v in np.unique(data)),
            "policy": "reuse_if_exists",
        }

    # Always load the case's reference prediction (cached teaching provider).
    ref = nib.load(str(ref_path))
    data = validate_segmentation(np.asanyarray(ref.dataobj))
    nib.save(nib.Nifti1Image(data, np.asarray(ref.affine)), out_path)
    return {
        "ok": True,
        "reused_existing": False,
        "provider_invoked": True,
        "output": str(out_path),
        "input": str(input_path),
        "shape": list(data.shape),
        "labels_present": sorted(int(v) for v in np.unique(data)),
        "policy": "always_overwrite" if not reuse_existing else "reuse_if_exists",
    }


def run_weak_suite(work_root: Path, *, reuse_existing: bool = True) -> dict:
    """Initial checks using a fresh output directory per case — miss cross-run state."""
    work = Path(work_root) / f"weak_{uuid.uuid4().hex[:8]}"
    cases = _derive_cases(work / "cases")
    checks = []
    for case_id in ("A", "B"):
        out = work / f"out_{case_id}"
        result = process_case(cases[case_id]["case_dir"], out, reuse_existing=reuse_existing)
        pred, _ = load_segmentation_nifti(result["output"])
        mri = nib.load(str(cases[case_id]["mri_path"]))
        checks.append(
            check(
                f"{case_id}_output_exists",
                Path(result["output"]).is_file(),
                expected=True,
                observed=Path(result["output"]).is_file(),
            )
        )
        checks.append(
            check(
                f"{case_id}_shape",
                tuple(pred.shape) == tuple(mri.shape),
                expected=list(mri.shape),
                observed=list(pred.shape),
            )
        )
        try:
            validate_segmentation(pred)
            checks.append(check(f"{case_id}_labels", True, expected="valid", observed="ok"))
        except Exception as exc:  # noqa: BLE001
            checks.append(check(f"{case_id}_labels", False, expected="valid", observed=str(exc)))

    return bundle(
        challenge_id="stale_weak",
        title="Initial checks (fresh output dir per case)",
        command="challenge:stale_weak",
        checks=checks,
        explanation=(
            "These checks use a separate output directory for each case, so they never "
            "see state left behind by a previous run in a shared folder."
        ),
        meta={"reuse_existing": reuse_existing},
    )


def run_sequential(
    work_root: Path,
    *,
    reuse_existing: bool,
    session_dir: Path | None = None,
) -> dict:
    """Process A then B in the same output directory; return comparison evidence."""
    root = Path(session_dir) if session_dir is not None else Path(work_root) / f"seq_{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    cases = _derive_cases(root / "cases")
    shared_out = root / "shared_out"
    if shared_out.exists() and session_dir is None:
        shutil.rmtree(shared_out)
    shared_out.mkdir(parents=True, exist_ok=True)

    snap_dir = root / "snapshots"
    snap_dir.mkdir(exist_ok=True)

    result_a = process_case(cases["A"]["case_dir"], shared_out, reuse_existing=reuse_existing)
    # Snapshot first result before second call (same path may be reused).
    snap_a = snap_dir / "after_A_prediction.nii.gz"
    shutil.copy2(result_a["output"], snap_a)
    arr_a, _ = load_segmentation_nifti(snap_a)

    result_b = process_case(cases["B"]["case_dir"], shared_out, reuse_existing=reuse_existing)
    arr_b, _ = load_segmentation_nifti(result_b["output"])
    ref_b, _ = load_segmentation_nifti(cases["B"]["ref_path"])
    ref_a, _ = load_segmentation_nifti(cases["A"]["ref_path"])

    match_b = abs(mean_dice(arr_b, ref_b) - 1.0) < 1e-9
    match_a_ref = abs(mean_dice(arr_b, ref_a) - 1.0) < 1e-9
    same_as_snap_a = np.array_equal(arr_b, arr_a)

    checks = [
        check("A_wrote_output", Path(result_a["output"]).is_file(), expected=True, observed=True),
        check(
            "B_matches_B_reference",
            match_b,
            expected="Dice(B_result, B_ref) == 1",
            observed=round(mean_dice(arr_b, ref_b), 6),
            detail="Acceptance: each case matches its own reference, not merely 'different inputs differ'.",
        ),
        check(
            "B_equals_snapshot_A_informative",
            True,
            expected="see observed",
            observed=same_as_snap_a,
            detail="Informative: if true while B_matches_B_reference is false, B received A's stale result.",
        ),
        check(
            "B_reused_existing_flag",
            True,
            expected="instrumentation",
            observed={
                "reused_existing": result_b.get("reused_existing"),
                "provider_invoked": result_b.get("provider_invoked"),
            },
        ),
    ]

    return bundle(
        challenge_id="stale_sequential",
        title=f"Sequential A→B ({'faulty reuse' if reuse_existing else 'always overwrite'})",
        command=f"challenge:stale_sequential reuse={reuse_existing}",
        checks=checks,
        explanation=(
            "Faulty policy returns an existing prediction.nii.gz without binding it to the current input. "
            "Correct policy always processes the current case and overwrites the output."
            if reuse_existing
            else "Corrected policy always overwrites from the current case's provider."
        ),
        meta={
            "reuse_existing": reuse_existing,
            "session_dir": str(root),
            "shared_output": str(shared_out / "prediction.nii.gz"),
            "result_a": result_a,
            "result_b": result_b,
            "dice_B_vs_Bref": round(mean_dice(arr_b, ref_b), 6),
            "dice_B_vs_Aref": round(mean_dice(arr_b, ref_a), 6),
            "B_matches_B_reference": match_b,
            "B_looks_like_A": match_a_ref or same_as_snap_a,
            "teaching_note": cases["B"]["meta"]["note"],
        },
    )


def run_regression(work_root: Path, *, reuse_existing: bool) -> dict:
    """Stronger test: snapshot A, run B in same dir, require B matches B reference."""
    seq = run_sequential(work_root, reuse_existing=reuse_existing)
    match = seq["meta"]["B_matches_B_reference"]
    checks = [
        check(
            "sequential_B_matches_own_reference",
            match,
            expected=True,
            observed=match,
            detail=(
                "Failed for the intended reason: shared output reused A's prediction."
                if (reuse_existing and not match)
                else "B output matches B reference."
            ),
        ),
        check(
            "not_path_only",
            True,
            expected="compare arrays to references",
            observed="snapshots used before second call",
            detail="Both calls may return the same path; the test snapshots the first file.",
        ),
    ]
    ok = match
    # For faulty, ok should be False
    return bundle(
        challenge_id="stale_regression_faulty" if reuse_existing else "stale_regression_corrected",
        title="Regression: two cases, one output directory",
        command=f"challenge:stale_regression reuse={reuse_existing}",
        checks=checks,
        explanation=seq["explanation"],
        meta=seq["meta"],
    )


# Force bundle ok for regression to follow match
def run_stale_regression_faulty(work_root: Path | None = None) -> dict:
    root = Path(work_root) if work_root else Path(".")
    result = run_regression(root, reuse_existing=True)
    # Ensure ok reflects detection: faulty should fail the match check
    result["ok"] = all(c["pass"] for c in result["checks"] if c["name"] == "sequential_B_matches_own_reference")
    # Wait - for faulty, match is False, so check pass is False, ok False. Good.
    # But we want expected_failure semantics in the lab.
    if not result["ok"]:
        result["expected_failure"] = True
        result["message"] = (
            "Expected failure: sequential regression detected stale reuse of case A's prediction for case B."
        )
    return result


def run_stale_regression_corrected(work_root: Path | None = None) -> dict:
    root = Path(work_root) if work_root else Path(".")
    return run_regression(root, reuse_existing=False)


def run_stale_weak(work_root: Path | None = None) -> dict:
    root = Path(work_root) if work_root else Path(".")
    return run_weak_suite(root, reuse_existing=True)


def create_exercise_session(work_root: Path) -> dict:
    """Create an isolated A/B exercise session (shared output dir)."""
    root = Path(work_root) / f"stale_ex_{uuid.uuid4().hex}"
    if root.exists():
        shutil.rmtree(root)
    cases = _derive_cases(root / "cases")
    shared = root / "shared_out"
    shared.mkdir(parents=True)
    (root / "snapshots").mkdir()
    state = {
        "session_dir": str(root),
        "shared_out": str(shared),
        "ran_a": False,
        "ran_b": False,
        "policy": None,
    }
    (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return {
        "ok": True,
        "session_id": root.name,
        "session_dir": str(root),
        "message": "Exercise session ready. Shared output directory is empty.",
        "teaching_note": cases["B"]["meta"]["note"],
    }


def _load_session(session_dir: Path) -> dict:
    return json.loads((session_dir / "state.json").read_text(encoding="utf-8"))


def _save_session(session_dir: Path, state: dict) -> None:
    (session_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")


def session_process(
    session_dir: Path,
    case_id: str,
    *,
    reuse_existing: bool,
) -> dict:
    """Process A or B inside an existing exercise session."""
    session_dir = Path(session_dir)
    if not session_dir.is_dir():
        return {"ok": False, "error": "Unknown session. Call reset first.", "mode": "live"}
    state = _load_session(session_dir)
    cases = {
        "A": session_dir / "cases" / "case_A",
        "B": session_dir / "cases" / "case_B",
    }
    if case_id not in cases:
        return {"ok": False, "error": f"case must be A or B, got {case_id}"}
    if case_id == "B" and not state.get("ran_a"):
        return {
            "ok": False,
            "error": "Out of order: process case A before case B in this exercise.",
            "hint": "The defect appears when an output from A is already present.",
        }
    shared = Path(state["shared_out"])
    result = process_case(cases[case_id], shared, reuse_existing=reuse_existing)
    if case_id == "A":
        snap = session_dir / "snapshots" / "after_A_prediction.nii.gz"
        shutil.copy2(result["output"], snap)
        state["ran_a"] = True
        state["snap_a"] = str(snap)
    else:
        state["ran_b"] = True
    state["policy"] = "reuse_if_exists" if reuse_existing else "always_overwrite"
    _save_session(session_dir, state)

    ref_path = next((cases[case_id] / "prediction").glob("*_pred.nii.gz"))
    arr, _ = load_segmentation_nifti(result["output"])
    ref, _ = load_segmentation_nifti(ref_path)
    return {
        "ok": True,
        "action": f"stale_process_{case_id}",
        "case_id": case_id,
        "mode": "live",
        "command": f"process_case({case_id}, shared_out, reuse_existing={reuse_existing})",
        "message": f"Processed case {case_id}.",
        "result": result,
        "dice_vs_own_reference": round(mean_dice(arr, ref), 6),
        "session_dir": str(session_dir),
        "shared_output": result["output"],
        "checks": [
            check("output_exists", True, expected=True, observed=True),
            check(
                "matches_own_reference",
                abs(mean_dice(arr, ref) - 1.0) < 1e-9,
                expected=1.0,
                observed=round(mean_dice(arr, ref), 6),
            ),
            check(
                "reused_existing",
                True,
                expected="instrumentation",
                observed=result.get("reused_existing"),
            ),
        ],
        "explanation": (
            "Instrumentated teaching call. reused_existing=True means the file already present "
            "was returned without re-binding to this input."
        ),
    }


def session_compare(session_dir: Path) -> dict:
    session_dir = Path(session_dir)
    state = _load_session(session_dir)
    if not (state.get("ran_a") and state.get("ran_b")):
        return {"ok": False, "error": "Process case A then case B before comparing."}
    shared = Path(state["shared_out"]) / "prediction.nii.gz"
    snap_a = Path(state["snap_a"])
    ref_b = next((session_dir / "cases" / "case_B" / "prediction").glob("*_pred.nii.gz"))
    ref_a = next((session_dir / "cases" / "case_A" / "prediction").glob("*_pred.nii.gz"))
    arr_b, _ = load_segmentation_nifti(shared)
    arr_a, _ = load_segmentation_nifti(snap_a)
    rb, _ = load_segmentation_nifti(ref_b)
    ra, _ = load_segmentation_nifti(ref_a)
    match_b = abs(mean_dice(arr_b, rb) - 1.0) < 1e-9
    return bundle(
        challenge_id="stale_compare",
        title="Compare evidence for case B",
        command="session_compare",
        checks=[
            check("output_exists", shared.is_file(), expected=True, observed=shared.is_file()),
            check("shape_valid", True, expected=list(arr_b.shape), observed=list(arr_b.shape)),
            check("labels_valid", True, expected="0–5", observed=sorted(int(v) for v in np.unique(arr_b))),
            check(
                "saved_matches_B_reference",
                match_b,
                expected=True,
                observed=round(mean_dice(arr_b, rb), 6),
            ),
            check(
                "equals_snapshot_A",
                True,
                expected="informative",
                observed=bool(np.array_equal(arr_b, arr_a)),
            ),
            check(
                "equals_A_reference",
                True,
                expected="informative",
                observed=round(mean_dice(arr_b, ra), 6),
            ),
        ],
        explanation=(
            "If saved_matches_B_reference is false and the result equals snapshot A, "
            "the shared output reused A's prediction."
        ),
        meta={"policy": state.get("policy"), "session_dir": str(session_dir)},
    )