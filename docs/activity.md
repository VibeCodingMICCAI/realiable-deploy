# Tutorial activity guide

**Audience:** medical imaging / ML researchers  
**Format:** quick 5–10 min or full ~30 min  

## Learning goals

1. Understand what the knee MRI segmentation tool inputs/outputs.  
2. See that green tests can miss **stale result reuse** across cases.  
3. Improve prompts/tests; review README as handover.  
4. Separate executed evidence from samples and reveals.

## Routes

- **Quick:** Intro → core challenge (stale reuse) → evidence summary  
- **Full:** Intro → core → layered testing menu → README handover → summary  

## 0. What does this tool do?

Packaged extract `examples/case_001` (downsampled). Interactive axial slices (subset exported). Cached tutorial path ≠ optional full nnU-Net inference.

## 1. Core — Changed input, unchanged result

Seeded defect: reuse `prediction.nii.gz` if present, without binding to the current input.  
Teaching cases A/B derived from the packaged extract (B remaps labels) — not two patients.

Steps: weak tests → predict → A then B same output dir → compare → stronger regression → always-overwrite fix.

## 2. Layered testing menu

L1 contracts · L2 mean vs per-label / optional affine · L3 provenance.

## 3. README handover

Incomplete vs improved README; audit prompt; optional pair cold-start.

## Launch

```bash
python -m pip install -e ".[test]"
python scripts/export_intro_slices.py   # if slice assets missing
python scripts/tutorial_lab.py
```
