"""Collect lightweight provenance for a reproducible run."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    canonical = np.ascontiguousarray(array)
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def git_commit(repo: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def collect_provenance(
    *,
    case_id: str,
    input_path: Path,
    output_path: Path | None = None,
    output_array: np.ndarray | None = None,
    config: dict[str, Any] | None = None,
    model_version: str = "nnUNet Dataset360_oaizib 3d_fullres (cached tutorial path)",
) -> dict[str, Any]:
    """Build a JSON-serialisable provenance record."""
    import nibabel

    from . import __version__

    record: dict[str, Any] = {
        "tool_version": __version__,
        "model_version": model_version,
        "git_commit": git_commit(Path(__file__).resolve().parents[2]),
        "data_case": case_id,
        "input_path": str(input_path),
        "input_sha256": file_sha256(Path(input_path)),
        "config": config or {"mode": "cached", "seed": None},
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "framework_versions": {
            "numpy": np.__version__,
            "nibabel": nibabel.__version__,
        },
    }
    if output_path is not None and Path(output_path).exists():
        record["output_path"] = str(output_path)
        record["output_file_sha256"] = file_sha256(Path(output_path))
    if output_array is not None:
        record["output_array_sha256"] = array_sha256(np.asarray(output_array))
    return record


def write_provenance(record: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
