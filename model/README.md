# Model notes

This tutorial wraps an **existing** knee MRI segmentation prototype based on
**nnU-Net v2** (`Dataset360_oaizib`, configuration `3d_fullres`).

## What the model does

Input: 3D knee MRI (`.nii.gz`)  
Output: multi-label segmentation with:

| Label | Structure |
|---:|---|
| 0 | background |
| 1 | Femur |
| 2 | Femoral Cartilage |
| 3 | Tibia |
| 4 | Medial Tibial Cartilage |
| 5 | Lateral Tibial Cartilage |

## Why checkpoints are not committed

Each fold checkpoint is roughly **250 MB**. Full-resolution knee MRI volumes are
also large (~20 MB each). For a public teaching repository we therefore:

- ship a **downsampled cached example** under `examples/case_001/`;
- keep real nnU-Net weights **outside** Git;
- treat live GPU/CPU inference as an **optional** advanced step.

## Local model path used during development

```text
C:\Users\chris\MICCAI2026\nnUNet\nnUNet_results\Dataset360_oaizib\nnUNetTrainer__nnUNetPlans__3d_fullres
```

Set:

```bash
set VIBE_NNUNET_MODEL=C:\path\to\nnUNetTrainer__nnUNetPlans__3d_fullres
```

Optional inference needs:

```bash
pip install -e ".[infer]"
```

and a working `nnUNetv2_predict` environment with `nnUNet_results` configured.

## Assumption

The live tutorial default path uses **cached predictions**. This is intentional:
the teaching goal is testing/reproducibility/readiness, not waiting for 3D
network inference during a 30-minute session.
