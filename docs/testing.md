# Testing the software around an AI model

See also: [Vibe coding recipes](vibe_coding_recipes.md) — how to prompt for tests
and score AI-generated tests yourself.

```text
Testing the AI model  ≠  Testing the AI software
```

| Model question | Software question |
|---|---|
| Is segmentation performance acceptable? | Does the image load correctly? |
| Is Dice high enough on a cohort? | Is preprocessing producing the expected shape? |
| Does the network generalise? | Does output align with the input grid? |
| | Can invalid data be detected? |
| | Can a code change silently alter previous results? |

This repository demonstrates a small set of software tests:

- smoke test of the cached pipeline;
- unit tests for loading, labels and Dice;
- invalid-input tests;
- regression protection for the packaged tutorial case.
