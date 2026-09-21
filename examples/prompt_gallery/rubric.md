# Rubric for scoring AI-generated software tests

Score each item **0** (no) or **1** (yes). Total out of **6**.

1. **Calls real path** — invokes project API such as `run_cached_pipeline` (not an empty shell).
2. **Fixed example** — binds `examples/case_001` (not only random synthetic data).
3. **Observable asserts** — checks files, shapes, labels, or Dice (not `assert True`).
4. **Regression anchor** — compares to `metrics.json` or output hash so silent drift fails.
5. **Failure modes** — covers missing/invalid inputs with clear errors.
6. **Tutorial constraints** — no model download, no GPU requirement, CI-friendly.
