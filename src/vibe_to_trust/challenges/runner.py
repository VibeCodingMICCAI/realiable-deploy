"""Challenge runners for the interactive tutorial lab."""

from __future__ import annotations

from pathlib import Path

from .affine import run_affine_challenge
from .levels import (
    run_level1_dice,
    run_level1_invalid,
    run_level1_shapes,
    run_level2_geometry,
    run_level2_per_label,
    run_level3_evidence,
)
from .stale_reuse import (
    run_sequential,
    run_stale_regression_corrected,
    run_stale_regression_faulty,
    run_stale_weak,
)

ALLOWED_CHALLENGES = frozenset(
    {
        "stale_weak",
        "stale_sequential_faulty",
        "stale_sequential_corrected",
        "stale_regression_faulty",
        "stale_regression_corrected",
        "affine_weak_faulty",
        "affine_weak_corrected",
        "affine_geometry_faulty",
        "affine_geometry_corrected",
        "level1_dice",
        "level1_shapes",
        "level1_invalid",
        "level2_geometry",
        "level2_per_label",
        "level3_evidence",
    }
)


def run_challenge(challenge_id: str, work_root: Path | None = None) -> dict:
    """Dispatch an allowlisted challenge and return a structured result dict."""
    if challenge_id not in ALLOWED_CHALLENGES:
        raise KeyError(f"challenge not allowed: {challenge_id}")

    mapping = {
        "stale_weak": lambda: run_stale_weak(work_root),
        "stale_sequential_faulty": lambda: run_sequential(Path(work_root or "."), reuse_existing=True),
        "stale_sequential_corrected": lambda: run_sequential(Path(work_root or "."), reuse_existing=False),
        "stale_regression_faulty": lambda: run_stale_regression_faulty(work_root),
        "stale_regression_corrected": lambda: run_stale_regression_corrected(work_root),
        "affine_weak_faulty": lambda: run_affine_challenge(variant="faulty", suite="weak", work_root=work_root),
        "affine_weak_corrected": lambda: run_affine_challenge(
            variant="corrected", suite="weak", work_root=work_root
        ),
        "affine_geometry_faulty": lambda: run_affine_challenge(
            variant="faulty", suite="geometry", work_root=work_root
        ),
        "affine_geometry_corrected": lambda: run_affine_challenge(
            variant="corrected", suite="geometry", work_root=work_root
        ),
        "level1_dice": lambda: run_level1_dice(work_root),
        "level1_shapes": lambda: run_level1_shapes(work_root),
        "level1_invalid": lambda: run_level1_invalid(work_root),
        "level2_geometry": lambda: run_level2_geometry(work_root),
        "level2_per_label": lambda: run_level2_per_label(work_root),
        "level3_evidence": lambda: run_level3_evidence(work_root),
    }
    return mapping[challenge_id]()
