from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from vibe_to_trust.preprocessing import InputError, load_mri


def test_rejects_wrong_dimensionality(tmp_path: Path):
    path = tmp_path / "bad.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros((8, 8), dtype=np.float32), np.eye(4)), path)
    with pytest.raises(InputError, match="3D"):
        load_mri(path)


def test_rejects_constant_image(tmp_path: Path):
    path = tmp_path / "const.nii.gz"
    nib.save(nib.Nifti1Image(np.ones((8, 8, 8), dtype=np.float32), np.eye(4)), path)
    with pytest.raises(InputError, match="no intensity variation"):
        load_mri(path)


def test_rejects_nonfinite_image(tmp_path: Path):
    data = np.ones((8, 8, 8), dtype=np.float32)
    data[0, 0, 0] = np.nan
    path = tmp_path / "nan.nii.gz"
    nib.save(nib.Nifti1Image(data, np.eye(4)), path)
    with pytest.raises(InputError, match="NaN or Inf"):
        load_mri(path)
