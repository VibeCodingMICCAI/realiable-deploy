"""Command-line entry points."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import webbrowser

import nibabel as nib
import numpy as np

from . import __version__
from .inference import EXAMPLE_CASE, run_cached_pipeline
from .metrics import mean_dice
from .preprocessing import load_mri
from .provenance import collect_provenance, write_provenance
from .visualisation import save_mid_slice_overlay


def _open_image(path: Path) -> None:
    """Open an image with the OS default viewer when possible."""
    resolved = path.resolve()
    try:
        if sys.platform.startswith("win"):
            os.startfile(resolved)  # type: ignore[attr-defined]
        else:
            webbrowser.open(resolved.as_uri())
    except OSError as exc:
        print(f"(Could not auto-open image: {exc})", flush=True)


def demo_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fast cached demo of the knee MRI prototype")
    parser.add_argument("--case", type=Path, default=EXAMPLE_CASE)
    parser.add_argument("--out", type=Path, default=Path("outputs/demo"))
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="do not open the overlay image automatically",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="also print the machine-readable JSON payload",
    )
    args = parser.parse_args(argv)

    result = run_cached_pipeline(args.case, args.out)
    image, _ = load_mri(next((args.case / "input").glob("*_mri.nii.gz")))
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    gt_path = next((args.case / "ground_truth").glob("*_gt.nii.gz"), None)
    gt = np.asanyarray(nib.load(gt_path).dataobj) if gt_path else None
    overlay = save_mid_slice_overlay(image, pred, args.out / "overlay.png", gt)
    packaged = Path("examples/case_001/overlay/mid_slice.png").resolve()

    metrics = result.get("metrics", {})
    print()
    print("=" * 64)
    print("  Knee MRI segmentation demo  (cached, CPU-friendly)")
    print("=" * 64)
    print()
    print("What you should look at:")
    print(f"  1. Overlay image : {overlay.resolve()}")
    print(f"  2. Packaged copy : {packaged}")
    print(f"  3. Prediction    : {Path(result['output']).resolve()}")
    print()
    print("Pipeline:")
    print("  MRI  ->  cached model output  ->  segmentation  ->  overlay")
    print()
    print("Dice on the tutorial case:")
    for name, value in metrics.items():
        if name == "mean_dice":
            continue
        print(f"  - {name:<28} {value:.3f}")
    if "mean_dice" in metrics:
        print(f"  - {'Mean Dice':<28} {metrics['mean_dice']:.3f}")
    print()
    print("Teaching note:")
    print("  This shows the prototype can produce a plausible result quickly.")
    print("  It does NOT prove clinical validity or full-resolution performance.")
    print()
    if args.json:
        print(json.dumps({**result, "overlay": str(overlay), "version": __version__}, indent=2))
    if not args.no_open:
        print("Opening overlay image...", flush=True)
        _open_image(overlay)
    return 0


def reproduce_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce the cached tutorial example")
    parser.add_argument("--case", type=Path, default=EXAMPLE_CASE)
    parser.add_argument("--out", type=Path, default=Path("outputs/reproduce"))
    args = parser.parse_args(argv)

    result = run_cached_pipeline(args.case, args.out)
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    gt = np.asanyarray(nib.load(next((args.case / "ground_truth").glob("*_gt.nii.gz"))).dataobj)
    dice = mean_dice(pred, gt)
    expected = json.loads((args.case / "metrics.json").read_text(encoding="utf-8"))
    expected_dice = float(expected["tutorial_resolution_dice"]["mean_dice"])
    record = collect_provenance(
        case_id=expected["case_id"],
        input_path=next((args.case / "input").glob("*_mri.nii.gz")),
        output_path=Path(result["output"]),
        output_array=pred,
        config={"mode": "cached", "expected_mean_dice": expected_dice},
    )
    record["measured_mean_dice"] = round(dice, 6)
    record["dice_matches_cached"] = abs(dice - expected_dice) < 1e-5
    write_provenance(record, args.out / "provenance.json")
    print(json.dumps(record, indent=2, sort_keys=True))
    if not record["dice_matches_cached"]:
        print("WARNING: measured Dice differs from cached metrics.", flush=True)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print("usage: python -m vibe_to_trust.cli [demo|reproduce] ...")
        return 0
    command, rest = argv[0], argv[1:]
    if command == "demo":
        return demo_main(rest)
    if command == "reproduce":
        return reproduce_main(rest)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
