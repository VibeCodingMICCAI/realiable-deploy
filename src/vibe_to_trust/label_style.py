"""Shared label colours for intro and challenge visuals."""

from __future__ import annotations

LABEL_NAMES = {
    0: "Background",
    1: "Femur",
    2: "Femoral Cartilage",
    3: "Tibia",
    4: "Medial Tibial Cartilage",
    5: "Lateral Tibial Cartilage",
}

# RGB in 0–1, matched to visualisation.save_mid_slice_overlay
LABEL_COLORS = {
    1: (1.0, 0.2, 0.2),
    2: (1.0, 0.85, 0.1),
    3: (0.2, 0.55, 1.0),
    4: (0.2, 0.9, 0.4),
    5: (0.9, 0.3, 0.9),
}

LABEL_COLORS_HEX = {
    1: "#ff3333",
    2: "#ffd91a",
    3: "#338cff",
    4: "#33e666",
    5: "#e64ce6",
}
