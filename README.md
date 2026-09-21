# From Vibe Coding to Trustworthy AI

### Testing, Reproducibility, and Readiness Using a Knee MRI Segmentation Prototype

```text
AI prototype
     ↓
Testing
     ↓
Reproducibility
     ↓
Readiness for intended use
```

We already have a knee MRI segmentation model that works. This repository asks a
different question:

> The AI works on my laptop. What do I need before I can trust it, share it,
> publish it, demonstrate it, or build real software around it?

## What this repository is

A **30-minute teaching repository** around an existing **nnU-Net v2** knee MRI
auto-segmentation prototype (`Dataset360_oaizib`).

It focuses on:

1. testing the software around the model;
2. reproducibility;
3. making a prototype shareable;
4. different levels of readiness for different intended uses.

## Quick start

```bash
python -m pip install -e ".[test]"
python scripts/tutorial_lab.py
```

That opens the interactive site at `http://127.0.0.1:8000` with:

- live **Run demo / smoke / reproduce** buttons (cached, CPU-friendly);
- a **Score AI-generated tests** exercise (weak / medium / strong prompts);
- the pack-by-intended-use game.

Or run the pieces from the terminal:

```bash
python scripts/demo.py
python scripts/run_tests.py
python scripts/reproduce_example.py
```

`python scripts/demo.py` prints a short human summary and opens
`outputs/demo/overlay.png`. Use `--no-open` for terminal-only output.

How we teach vibe-coding tests & repro scripts:
[`docs/vibe_coding_recipes.md`](docs/vibe_coding_recipes.md)
and [`examples/prompt_gallery/`](examples/prompt_gallery/).

**Full activity sheet (facilitators + participants):**
[`docs/activity.md`](docs/activity.md) · on the site: [`website/activity.html`](website/activity.html)

Or:

```bash
python scripts/run.py setup
python scripts/run.py demo
python scripts/run.py test
python scripts/run.py reproduce
```

## Interactive tutorial (GitHub Pages)

Local (recommended for live buttons):

```bash
python scripts/tutorial_lab.py
```

Static preview only:

```bash
python -m http.server 8000 --directory website
```

Then visit `http://localhost:8000` (lab buttons fall back to pre-recorded samples
unless you use `tutorial_lab.py`).

To publish: GitHub → Settings → Pages → deploy from GitHub Actions
(`.github/workflows/pages.yml` uploads the `website/` folder), or deploy the
`website/` folder as Pages content.

## The knee MRI prototype

- Framework: **nnU-Net v2 / PyTorch**
- Task: multi-label knee MRI segmentation
- Labels: Femur, Femoral Cartilage, Tibia, Medial/Lateral Tibial Cartilage
- Live tutorial path: **cached downsampled example** in `examples/case_001/`
- Optional real inference: local model folder + `pip install -e ".[infer]"`  
  See [`model/README.md`](model/README.md)

## Important distinction

```text
Testing the AI model  ≠  Testing the AI software
```

Model question: “Is segmentation performance acceptable?”  
Software questions: loading, preprocessing, alignment, invalid inputs, saving,
reproducing, detecting regressions after AI-assisted edits.

## What this tutorial is NOT

- not a segmentation-model training tutorial;
- not a claim of state-of-the-art segmentation;
- not clinical software certification;
- not regulatory compliance guidance.

Clinical readiness requires much more than software testing.

## Repository map

```text
src/vibe_to_trust/   lightweight software helpers
examples/case_001/   cached MRI, GT, prediction, overlay, metrics
examples/prompt_gallery/  weak/medium/strong prompts + scored test examples
tests/               smoke / unit / integration / regression / invalid-input
scripts/             demo, reproduce, provenance, tests, tutorial_lab
model/               metadata + how to attach local nnU-Net weights
docs/                short notes + vibe coding recipes
website/             interactive tutorial (+ live lab when using tutorial_lab.py)
```

## Model and data policy

Do **not** commit full nnU-Net checkpoints (~250 MB each) or full-resolution MRI
volumes (~20 MB each) unless you have an explicit distribution plan.

This repository ships a small tutorial extract only. Point `VIBE_NNUNET_MODEL`
at your local results folder for optional full inference.
