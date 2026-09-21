#!/usr/bin/env python
"""Collect provenance for the cached tutorial example."""

from __future__ import annotations

import json
from pathlib import Path

from vibe_to_trust.inference import EXAMPLE_CASE, run_cached_pipeline
from vibe_to_trust.provenance import collect_provenance, write_provenance
import nibabel as nib
import numpy as np


def main() -> int:
    out = Path("outputs/provenance")
    result = run_cached_pipeline(EXAMPLE_CASE, out)
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    metrics = json.loads((EXAMPLE_CASE / "metrics.json").read_text(encoding="utf-8"))
    record = collect_provenance(
        case_id=metrics["case_id"],
        input_path=next((EXAMPLE_CASE / "input").glob("*_mri.nii.gz")),
        output_path=Path(result["output"]),
        output_array=pred,
    )
    path = write_provenance(record, out / "provenance.json")
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
