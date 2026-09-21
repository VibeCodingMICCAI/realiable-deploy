# Why this score is low

- `assert True` always passes.
- Random arrays are not `examples/case_001`.
- Never calls `run_cached_pipeline`.
- No regression anchor, no invalid-input checks.
- A broken pipeline would still look green.
