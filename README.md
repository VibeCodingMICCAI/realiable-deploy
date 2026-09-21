# From Vibe Coding to Trustworthy AI

### Knee MRI segmentation: tool intro, stale-result testing, README handover

Interactive MICCAI stand. Default path uses a **cached** downsampled extract (`examples/case_001`) — not clinical certification.

## Quick start

```bash
python -m pip install -e ".[test]"
python scripts/export_intro_slices.py
python scripts/tutorial_lab.py
```

Open `http://127.0.0.1:8000` (`/activity.html` for the written guide).

| Activity | Focus |
|---|---|
| Intro | What the tool inputs/outputs (real slices) |
| Core | Changed input, unchanged result (seeded reuse bug) |
| Menu | Optional layered tests |
| README | Collaborator handover review |

## Terminal commands

```bash
python scripts/demo.py --no-open
python scripts/run_tests.py
python scripts/reproduce_example.py
```

Expected demo outputs: `outputs/demo/prediction.nii.gz`, `outputs/demo/overlay.png`.

## Cached vs optional real inference

- **Default:** cached pipeline on `examples/case_001/`.
- **Optional:** `pip install -e ".[infer]"` + `VIBE_NNUNET_MODEL` — see `model/README.md`.

## Guides

- [`docs/activity.md`](docs/activity.md) · [`docs/coordinator_zh.md`](docs/coordinator_zh.md) (中文协调员)  
- [`docs/vibe_coding_recipes.md`](docs/vibe_coding_recipes.md)

## Verification

```bash
python -m pytest -q
```

## Limitations

- Tutorial volumes are downsampled.  
- Live lab ≠ fresh nnU-Net inference.  
- Teaching cases A/B for the core challenge are **derivatives** of the packaged extract.  
- Research sharing ≠ production ≠ clinical use.
