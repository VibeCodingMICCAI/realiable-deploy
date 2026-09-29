# Tutorial activity guide

**Audience:** medical imaging / ML researchers at a MICCAI interactive stand  
**Format:** one facilitator-led session, ~20 minutes  
**Language:** participant-facing content in English

## Narrative

> We have built a knee MRI segmentation tool with AI assistance. What should we test, and how can AI help us write useful tests?

## Learning goals

1. See what the tool inputs and outputs (cached demo, not fresh inference by default).
2. Define expected behaviours before sharing the tool.
3. Use two focused examples (mean Dice hide; unbound overlay) to improve test prompts and verify them.

## Timing

| Activity | Time | Focus |
|---|---|---|
| 1 · Explore the tool | ~5 min | MRI / mask / overlay; what should we check? |
| 2 · Generate useful tests | ~15 min | Mean Dice hide + overlay mismatch |

## Activity 1 — Explore the tool

- Show input MRI, segmentation mask, and overlay.
- Note: precomputed predictions; not fresh nnU-Net by default.
- Discussion: what should we check?
- Transition: demos show one run; tests check behaviours repeatedly.

## Activity 2 — Generate useful tests

### Example 1 — Mean Dice can hide a missing structure

Teaching prediction removes Lateral Tibial Cartilage (label 5). Mean Dice can still look acceptable (~0.75) while label-5 Dice = 0.

1. Vague mean-only checks **pass**.
2. Inspect mean vs per-label.
3. Stronger per-label gate **fails** on the faulty gate (expected failure).
4. Corrected gate **passes** on the full packaged prediction.

### Example 2 — Overlay may not match the saved segmentation

Teaching exporter writes a correct `prediction.nii.gz` but `overlay.png` from the wrong axial slice.

1. File-existence checks **pass**.
2. Compare overlay to a regenerated mid-slice overlay.
3. Stronger content check **fails** on unbound export; **passes** when rebound.

Production cached demo path stays separate; these are seeded teaching defects.

Close on the same page: define expected behaviour, generate a focused test, verify it detects the defect.

## Launch

```bash
python -m pip install -e ".[test]"
python scripts/export_intro_slices.py   # if slice assets missing
python scripts/export_stand_samples.py  # if teaching PNGs / samples missing
python scripts/tutorial_lab.py
```

## Optional further examples

Stale-result reuse, affine geometry, level 1–3 challenges — see `website/further.html` and `docs/vibe_coding_recipes.md`.

Facilitator notes: [`docs/facilitator.md`](facilitator.md).

## Caution

Completing this stand does not verify the entire tool or establish clinical readiness.
