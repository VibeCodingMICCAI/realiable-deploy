#!/usr/bin/env python
"""Export teaching PNGs and pre-recorded challenge samples for the stand."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEACHING = ROOT / "website" / "assets" / "teaching"
SAMPLES = ROOT / "website" / "assets" / "samples"


def main() -> int:
    from vibe_to_trust.challenges import run_challenge
    from vibe_to_trust.challenges.stand_examples import export_teaching_assets

    paths = export_teaching_assets(TEACHING)
    print("Teaching assets:")
    for k, v in paths.items():
        print(f"  {k}: {v}")

    ids = [
        "mean_dice_weak",
        "mean_dice_reveal",
        "mean_dice_regression_faulty",
        "mean_dice_regression_corrected",
        "overlay_weak",
        "overlay_reveal",
        "overlay_regression_faulty",
        "overlay_regression_corrected",
    ]
    SAMPLES.mkdir(parents=True, exist_ok=True)
    work = ROOT / "outputs" / "lab" / "sample_gen_stand"
    work.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        result = run_challenge(cid, work_root=work / cid)
        result["mode"] = "sample"
        out = SAMPLES / f"{cid}.json"
        out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"Sample {cid}: ok={result.get('ok')} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
