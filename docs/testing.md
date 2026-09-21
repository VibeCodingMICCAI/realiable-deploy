# Testing the software around an AI model

See also: [activity guide](activity.md), [vibe coding recipes](vibe_coding_recipes.md).

```text
Testing the AI model  ≠  Testing the AI software
```

| Model question | Software question |
|---|---|
| Is segmentation performance acceptable? | Does the image load correctly? |
| Is Dice high enough on a cohort? | Is the saved NIfTI affine preserved? |
| Does the network generalise? | Can invalid data be detected? |
| | Can a code change silently alter previous results? |

Core teaching challenge: weak export tests (file / shape / labels / array Dice)
can pass while spatial geometry is wrong. See `vibe_to_trust.challenges.affine`.

Empty-mask Dice convention in this repo: both empty → `1.0` (document before mean aggregation).
