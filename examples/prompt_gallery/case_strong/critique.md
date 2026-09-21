# Why this scores high

- Calls `run_cached_pipeline` on the packaged case.
- Checks shape, labels, and Dice against `metrics.json`.
- Stays cached / CPU-friendly.
- Still missing dedicated invalid-input tests (see `tests/test_invalid_inputs.py`) — that is the remaining gap vs a full suite.
