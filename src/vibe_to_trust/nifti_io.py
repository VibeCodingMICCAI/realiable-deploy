"""NIfTI save/load helpers with a narrow teaching seam for affine defects."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from .preprocessing import validate_segmentation


def save_segmentation_nifti(
    data: np.ndarray,
    affine: np.ndarray,
    path: Path | str,
    *,
    use_identity_affine: bool = False,
) -> Path:
    """Save a segmentation as NIfTI.

    Production callers must leave ``use_identity_affine=False``.
    The teaching flag forces an identity affine while keeping the array values —
    used only by the affine challenge's faulty variant.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mask = validate_segmentation(data)
    write_affine = np.eye(4) if use_identity_affine else np.asarray(affine, dtype=float)
    nib.save(nib.Nifti1Image(mask, write_affine), path)
    return path


def load_segmentation_nifti(path: Path | str) -> tuple[np.ndarray, np.ndarray]:
    """Reload a saved segmentation and return ``(data, affine)``."""
    path = Path(path)
    image = nib.load(str(path))
    data = validate_segmentation(np.asanyarray(image.dataobj))
    return data, np.asarray(image.affine, dtype=float)


def affines_match(
    a: np.ndarray,
    b: np.ndarray,
    *,
    rtol: float = 0.0,
    atol: float = 1e-5,
) -> bool:
    """Compare affines with an explicit numeric tolerance."""
    return bool(np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), rtol=rtol, atol=atol))
