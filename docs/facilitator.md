# Facilitator guide

English guide for running the MICCAI stand (~20 minutes). Participant UI is English.

## Elevator pitch

> We built a knee MRI segmentation tool. What should we check, and how can AI help write useful tests?  
> Default path uses a **cached** extract (not live full nnU-Net).  
> Two teaching defects: (1) mean Dice hides a missing structure; (2) overlay PNG unbound from the mid-slice prediction.  
> Not clinical certification.

## Setup

From the **repository root**:

```bash
python -m pip install -e ".[test]"
python scripts/export_intro_slices.py   # if intro slices are missing
python scripts/export_stand_samples.py  # optional: refresh teaching PNGs / sample JSON
python scripts/tutorial_lab.py
```

Open `http://127.0.0.1:8000` and hard-refresh (Ctrl+F5). Confirm:

- Activity 1: slice slider works.
- Activity 2 Example 1: initial checks pass; inspect shows label 5 = 0; faulty expected failure; corrected passes.
- Activity 2 Example 2: initial checks pass; compare shows wrong slice; faulty expected failure; corrected passes.

## Activities

| Activity | Time | Focus |
|---|---|---|
| 1 · Explore | ~5 min | MRI / mask / overlay; discuss what to check |
| 2 · Generate tests | ~15 min | Both examples: weak checks → reveal → stronger fail/pass |

### Example 1

Mean-only gate stays green while Lateral Tibial Cartilage (label 5) is missing. Fix: require a per-label Dice floor.

### Example 2

Overlay file exists but was written from the wrong axial slice. Fix: always regenerate overlay from the current prediction at the intended slice.

Stale-result reuse (A then B) is optional — see Further examples.

## Close

Define expected behaviour → focused test → verify it catches the defect.  
Distinguish live execution, pre-recorded samples, and expected failures. Research sharing ≠ production ≠ clinical use.
