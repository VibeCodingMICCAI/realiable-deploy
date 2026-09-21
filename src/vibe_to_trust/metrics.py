"""Simple segmentation metrics for teaching."""

from __future__ import annotations

import numpy as np


def dice_score(prediction: np.ndarray, reference: np.ndarray, label: int) -> float:
    """Dice coefficient for one integer label."""
    pred = np.asarray(prediction) == label
    ref = np.asarray(reference) == label
    denom = int(pred.sum() + ref.sum())
    if denom == 0:
        return 1.0
    return float(2 * np.logical_and(pred, ref).sum() / denom)


def mean_dice(
    prediction: np.ndarray,
    reference: np.ndarray,
    labels: tuple[int, ...] = (1, 2, 3, 4, 5),
) -> float:
    """Average Dice across foreground labels."""
    scores = [dice_score(prediction, reference, label) for label in labels]
    return float(np.mean(scores))
