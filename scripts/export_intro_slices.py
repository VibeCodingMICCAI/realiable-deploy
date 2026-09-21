#!/usr/bin/env python
"""Export lightweight axial slice PNGs for the website tool introduction."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

from vibe_to_trust.inference import EXAMPLE_CASE
from vibe_to_trust.label_style import LABEL_COLORS, LABEL_COLORS_HEX, LABEL_NAMES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "website" / "assets" / "intro_slices"
STEP = 4  # export every 4th slice → 16 of 64


def _norm_slice(base: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(base, (1, 99))
    return np.clip((base - lo) / (hi - lo + 1e-6), 0, 1)


def _overlay(base: np.ndarray, mask: np.ndarray) -> np.ndarray:
    rgb = np.stack([base, base, base], axis=-1)
    for label, color in LABEL_COLORS.items():
        m = mask == label
        for c, v in enumerate(color):
            rgb[:, :, c] = np.where(m, 0.45 * rgb[:, :, c] + 0.55 * v, rgb[:, :, c])
    return rgb


def _save_png(arr: np.ndarray, path: Path, cmap: str | None = "gray") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(2.4, 2.4), dpi=100)
    if arr.ndim == 2:
        ax.imshow(arr.T, origin="lower", cmap=cmap, vmin=0, vmax=5 if cmap != "gray" else None)
    else:
        ax.imshow(arr.transpose(1, 0, 2), origin="lower")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(path, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def main() -> int:
    mri_path = next((EXAMPLE_CASE / "input").glob("*_mri.nii.gz"))
    pred_path = next((EXAMPLE_CASE / "prediction").glob("*_pred.nii.gz"))
    gt_path = next((EXAMPLE_CASE / "ground_truth").glob("*_gt.nii.gz"))
    mri_img = nib.load(str(mri_path))
    pred_img = nib.load(str(pred_path))
    gt_img = nib.load(str(gt_path))
    mri = np.asanyarray(mri_img.dataobj).astype(np.float32)
    pred = np.asanyarray(pred_img.dataobj).astype(np.uint8)
    gt = np.asanyarray(gt_img.dataobj).astype(np.uint8)
    aff = np.asarray(mri_img.affine, dtype=float)
    spacing = [float(np.linalg.norm(aff[:3, i])) for i in range(3)]

    indices = list(range(0, mri.shape[2], STEP))
    OUT.mkdir(parents=True, exist_ok=True)
    for z in indices:
        base = _norm_slice(mri[:, :, z])
        _save_png(base, OUT / f"mri_{z:03d}.png", cmap="gray")
        _save_png(pred[:, :, z], OUT / f"pred_{z:03d}.png", cmap="nipy_spectral")
        _save_png(_overlay(base, pred[:, :, z]), OUT / f"overlay_{z:03d}.png", cmap=None)
        _save_png(gt[:, :, z], OUT / f"gt_{z:03d}.png", cmap="nipy_spectral")
        _save_png(_overlay(base, gt[:, :, z]), OUT / f"gt_overlay_{z:03d}.png", cmap=None)

    meta = {
        "case_id": "oaizib_405",
        "note": "Packaged tutorial extract from examples/case_001. Intentionally downsampled.",
        "file_format": ".nii.gz",
        "volume_shape": list(mri.shape),
        "voxel_spacing_mm": [round(s, 4) for s in spacing],
        "view_axis": "axial (index along axis 2)",
        "slice_indices": indices,
        "slice_count_exported": len(indices),
        "slice_count_total": int(mri.shape[2]),
        "export_step": STEP,
        "labels": {str(k): v for k, v in LABEL_NAMES.items() if k > 0},
        "label_colors_hex": {str(k): v for k, v in LABEL_COLORS_HEX.items()},
        "outputs_described": [
            {"path": "outputs/demo/prediction.nii.gz", "role": "Saved segmentation labels (NIfTI)"},
            {"path": "outputs/demo/overlay.png", "role": "Visual mid-slice overlay (PNG, not the clinical result)"},
            {"path": "outputs/reproduce/provenance.json", "role": "Provenance / verification record"},
        ],
        "asset_pattern": {
            "mri": "assets/intro_slices/mri_{index:03d}.png",
            "pred": "assets/intro_slices/pred_{index:03d}.png",
            "overlay": "assets/intro_slices/overlay_{index:03d}.png",
            "gt": "assets/intro_slices/gt_{index:03d}.png",
            "gt_overlay": "assets/intro_slices/gt_overlay_{index:03d}.png",
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (ROOT / "website" / "assets" / "intro_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {len(indices)} slice sets to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
