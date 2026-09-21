# Tutorial example case

`case_001` is a **downsampled** extract from `oaizib_405` in Dataset360_oaizib.

```text
examples/case_001/
  input/oaizib_405_mri.nii.gz
  ground_truth/oaizib_405_gt.nii.gz
  prediction/oaizib_405_pred.nii.gz
  overlay/mid_slice.png
  metrics.json
```

- Full-resolution mean Dice (from original ensemble prediction): see `metrics.json`
- Tutorial-resolution volume shape: `64 x 64 x 64`
- Purpose: live demo, GitHub Pages visuals, CPU-friendly tests

This is teaching data, not a clinical validation set.
