# Reproducibility

See [activity guide](activity.md) and the interactive lab
(`python scripts/tutorial_lab.py`).

Ideal research workflow:

```text
Clone
  ↓
Install
  ↓
Run one command
  ↓
Reproduce the example result
```

In this repository:

```bash
python -m pip install -e ".[test]"
python scripts/demo.py --no-open
python scripts/reproduce_example.py
python scripts/collect_provenance.py
```

`reproduce_example.py` writes provenance JSON with tool version, hashes, and
Dice vs the packaged extract. File-byte equality is stricter than semantic
equivalence (arrays + geometry + metrics) — see Level 3 in the tutorial.
