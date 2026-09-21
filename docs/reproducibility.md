# Reproducibility

See also: [Vibe coding recipes](vibe_coding_recipes.md) and the interactive lab
(`python scripts/tutorial_lab.py` → **Reproduce example**).

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
python scripts/demo.py
python scripts/reproduce_example.py
python scripts/collect_provenance.py
```

`reproduce_example.py` writes a provenance JSON with:

- tool version;
- model/version label;
- git commit when available;
- input hash;
- output hash;
- dependency versions;
- measured Dice vs cached Dice.
