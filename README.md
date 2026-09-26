# From Vibe Coding to Trustworthy AI

### Knee MRI segmentation: explore the tool, write useful tests, hand over with a README

Facilitator-led MICCAI stand (~25–30 minutes). Default path uses a **cached** downsampled extract (`examples/case_001`) — not clinical certification, and not fresh nnU-Net inference by default.

## Clone and run

```bash
git clone https://github.com/VibeCodingMICCAI/realiable-deploy.git
cd realiable-deploy
python -m pip install -e ".[test]"
python scripts/tutorial_lab.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Run all commands from the **repository root**.

If intro MRI slices are missing after a sparse checkout:

```bash
python scripts/export_intro_slices.py
```

Teaching preview images are created automatically on lab start if needed (or run `python scripts/export_stand_samples.py`).

## What this tool does

- **Input:** a 3D knee MRI as `.nii.gz` (see `examples/case_001/`).
- **Output:** a segmentation label map (`outputs/demo/prediction.nii.gz`) and a mid-slice overlay PNG (`outputs/demo/overlay.png`).
- **Limitation:** tutorial volumes are intentionally downsampled; research-sharing practice, not production or clinical software.

### Useful commands

| Goal | Command | Where to look |
|---|---|---|
| Run the cached demo | `python scripts/demo.py --no-open` | `outputs/demo/` |
| Run automated checks | `python scripts/run_tests.py` | terminal pass/fail |
| Open the stand | `python scripts/tutorial_lab.py` | browser |

Also useful: `python scripts/reproduce_example.py` → `outputs/reproduce/`.

## Cached demo vs real inference

- **Default / stand:** precomputed prediction for the packaged case.
- **Optional real inference:** `pip install -e ".[infer]"` and configure `VIBE_NNUNET_MODEL` — see [`model/README.md`](model/README.md).

## Three activities

1. **Explore the tool** — MRI / mask / overlay; what should we check before handover?
2. **Generate useful tests** — mean score can hide a missing structure; overlay may not match the saved segmentation.
3. **Hand over the tool** — what a useful README must answer.

Guides: [`docs/activity.md`](docs/activity.md) · [`docs/facilitator.md`](docs/facilitator.md)  
Prompt recipes (optional): [`docs/vibe_coding_recipes.md`](docs/vibe_coding_recipes.md)

## Verification

```bash
python -m pytest -q
```

Live lab buttons execute allowlisted Python on this machine. Sample / static mode shows **pre-recorded** results and labels them as such. Completing the stand does **not** verify the entire tool or clinical readiness.

## Limitations

- Teaching defects in Activity 2 are seeded for the stand (mean-only gate; unbound overlay).
- Live lab ≠ fresh nnU-Net inference.
- Research sharing ≠ production ≠ clinical use.
