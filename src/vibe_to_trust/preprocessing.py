"""Lightweight preprocessing helpers used by tests and demos."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np


class InputError(ValueError):
    """Raised when an input fails the documented software contract."""


def load_mri(path: Path | str) -> tuple[np.ndarray, np.ndarray]:
    """Load a 3D NIfTI MRI and return ``(data, affine)``."""
    path = Path(path)
    if not path.is_file():
        raise InputError(f"input file does not exist: {path}")
    try:
        image = nib.load(str(path))
    except Exception as exc:  # nibabel raises several IO-related errors
        raise InputError(f"could not read NIfTI input: {exc}") from exc
    if len(image.shape) != 3:
        raise InputError(f"expected a 3D image, got shape {image.shape}")
    data = np.asarray(image.get_fdata(dtype=np.float32))
    if data.size == 0:
        raise InputError("image is empty")
    if not np.all(np.isfinite(data)):
        raise InputError("image contains NaN or Inf")
    if float(np.ptp(data)) == 0:
        raise InputError("image has no intensity variation")
    return data, np.asarray(image.affine)


def validate_segmentation(mask: np.ndarray, allowed_labels: set[int] | None = None) -> np.ndarray:
    """Validate a segmentation mask and return it as ``uint8``."""
    array = np.asarray(mask)
    if array.ndim != 3:
        raise InputError(f"segmentation must be 3D, got shape {array.shape}")
    if not np.isfinite(array).all():
        raise InputError("segmentation contains NaN or Inf")
    if not np.all(np.equal(np.mod(array, 1), 0)):
        raise InputError("segmentation contains non-integer labels")
    labels = set(int(v) for v in np.unique(array))
    allowed = allowed_labels or {0, 1, 2, 3, 4, 5}
    unexpected = labels - allowed
    if unexpected:
        raise InputError(f"unexpected segmentation labels: {sorted(unexpected)}")
    return array.astype(np.uint8)


def zscore(data: np.ndarray) -> np.ndarray:
    """Simple intensity normalisation used in unit tests."""
    mean = float(np.mean(data))
    std = float(np.std(data))
    if std == 0:
        raise InputError("cannot z-score a constant image")
    return ((data - mean) / std).astype(np.float32)
