"""Simple visualisation helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def save_mid_slice_overlay(
    image: np.ndarray,
    prediction: np.ndarray,
    output_path: Path | str,
    ground_truth: np.ndarray | None = None,
) -> Path:
    """Save a mid-slice PNG comparing MRI / GT / prediction overlay."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    z = image.shape[2] // 2
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

    cols = 3 if ground_truth is not None else 2
    fig, axes = plt.subplots(1, cols, figsize=(3.4 * cols, 3.4), dpi=120)
    if cols == 2:
        axes = list(axes)
    axes[0].imshow(base.T, origin="lower", cmap="gray")
    axes[0].set_title("MRI")
    axes[0].axis("off")
    if ground_truth is not None:
        axes[1].imshow(ground_truth[:, :, z].T, origin="lower", cmap="nipy_spectral", vmin=0, vmax=5)
        axes[1].set_title("Ground truth")
        axes[1].axis("off")
        axes[2].imshow(overlay.transpose(1, 0, 2), origin="lower")
        axes[2].set_title("Prediction")
        axes[2].axis("off")
    else:
        axes[1].imshow(overlay.transpose(1, 0, 2), origin="lower")
        axes[1].set_title("Prediction")
        axes[1].axis("off")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
