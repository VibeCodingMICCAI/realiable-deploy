"""Inference wrappers.

Default path uses cached tutorial predictions so the live demo stays CPU-fast.
Optional real nnU-Net inference is available when the environment is configured.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import nibabel as nib
import numpy as np

from .preprocessing import InputError, load_mri, validate_segmentation


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CASE = ROOT / "examples" / "case_001"
DEFAULT_LABELS = {0, 1, 2, 3, 4, 5}


def load_cached_prediction(case_dir: Path = EXAMPLE_CASE) -> tuple[np.ndarray, np.ndarray]:
    """Load the packaged cached prediction for the tutorial case."""
    pred_path = next((case_dir / "prediction").glob("*_pred.nii.gz"))
    image = nib.load(str(pred_path))
    data = validate_segmentation(np.asanyarray(image.dataobj), DEFAULT_LABELS)
    return data, np.asarray(image.affine)


def run_cached_pipeline(case_dir: Path = EXAMPLE_CASE, output_dir: Path | None = None) -> dict:
    """Smoke-friendly pipeline that uses the cached prediction."""
    case_dir = Path(case_dir)
    input_path = next((case_dir / "input").glob("*_mri.nii.gz"))
    image, affine = load_mri(input_path)
    prediction, pred_affine = load_cached_prediction(case_dir)
    if image.shape != prediction.shape:
        raise InputError(
            f"cached prediction shape {prediction.shape} does not match image {image.shape}"
        )
    if not np.allclose(affine, pred_affine, atol=1e-5):
        raise InputError("cached prediction affine does not match input affine")

    if output_dir is None:
        output_dir = ROOT / "outputs" / "demo"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "prediction.nii.gz"
    nib.save(nib.Nifti1Image(prediction, affine), out_path)

    metrics_path = case_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    return {
        "mode": "cached",
        "input": str(input_path),
        "output": str(out_path),
        "shape": list(prediction.shape),
        "labels_present": sorted(int(v) for v in np.unique(prediction)),
        "metrics": metrics.get("tutorial_resolution_dice", {}),
    }


def run_nnunet_inference(
    input_image: Path,
    output_dir: Path,
    model_folder: Path | None = None,
    folds: tuple[int, ...] = (0,),
) -> Path:
    """Optional real inference via ``nnUNetv2_predict``.

    Requires the ``infer`` optional dependencies and a local model folder.
    """
    input_image = Path(input_image)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_folder = Path(
        model_folder
        or os.environ.get(
            "VIBE_NNUNET_MODEL",
            r"C:\Users\chris\MICCAI2026\nnUNet\nnUNet_results\Dataset360_oaizib\nnUNetTrainer__nnUNetPlans__3d_fullres",
        )
    )
    if not model_folder.is_dir():
        raise InputError(
            "nnU-Net model folder not found. Set VIBE_NNUNET_MODEL or install/pass model_folder."
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # nnU-Net expects <case>_0000.nii.gz inside an input folder.
        staged = tmp_path / "oaizib_demo_0000.nii.gz"
        shutil.copy2(input_image, staged)
        cmd = [
            "nnUNetv2_predict",
            "-i",
            str(tmp_path),
            "-o",
            str(output_dir),
            "-d",
            "360",
            "-c",
            "3d_fullres",
            "-f",
            *[str(f) for f in folds],
            "-chk",
            "checkpoint_final.pth",
        ]
        # Point predictor at the provided model by using results folder layout.
        env = os.environ.copy()
        results_root = model_folder.parents[1]  # .../nnUNet_results
        env["nnUNet_results"] = str(results_root)
        completed = subprocess.run(cmd, env=env, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise InputError(
                "nnUNetv2_predict failed. Ensure nnunetv2 is installed and model paths are set.\n"
                + completed.stderr
            )
    prediction = output_dir / "oaizib_demo.nii.gz"
    if not prediction.exists():
        # nnU-Net may write without suffix consistency; pick first NIfTI.
        candidates = list(output_dir.glob("*.nii.gz"))
        if not candidates:
            raise InputError("nnU-Net finished but no prediction NIfTI was found")
        prediction = candidates[0]
    return prediction
