# Tutorial activity: From Vibe Coding to Trustworthy AI

**Audience:** MICCAI / ML researchers who already have a working AI prototype  
**Format:** ~30–40 minutes (interactive website + optional local lab)  
**Example:** knee MRI multi-structure segmentation (nnU-Net, cached demo)

## Learning goals

By the end, participants can:

1. Separate **model testing** from **software testing** around an AI pipeline.
2. Name what makes a prototype **reproducible** (one command → same example result).
3. Use **better prompts** to generate tests, and **score** AI-generated tests with a rubric.
4. Match evidence to **intended use** (demo ≠ open-source ≠ clinical/production).

## What you need

| Mode | Command | What works |
|---|---|---|
| **Live lab (recommended)** | `python -m pip install -e ".[test]"` then `python scripts/tutorial_lab.py` | Interactive site + real cached demo / smoke / reproduce |
| **Static GitHub Pages** | Open the published site | Full UI; lab buttons use pre-recorded samples |
| **Static local preview** | `python -m http.server 8000 --directory website` | Same as Pages (sample lab) |

Interactive site (local): http://127.0.0.1:8000  
Activity page (this guide on the site): http://127.0.0.1:8000/activity.html  

## Flow at a glance

```text
1. Intended use
2. Testing checklist
3. Reproducibility checklist
4. Run the lab (demo / smoke / reproduce)
5. Score AI-generated tests (weak / medium / strong prompts)
6. Pack evidence by scenario (demo / open-source / clinical)
7. Summary
```

Suggested timing:

| Step | Minutes | Screen |
|---|---|---|
| Framing + intended use | 5 | Landing → Use |
| Testing vs software testing | 5 | Testing |
| Reproducibility | 4 | Repro |
| Run the lab | 6 | Lab |
| Score generated tests | 8 | Assess |
| Pack the bag | 6 | Scenarios |
| Debrief / summary | 4 | Summary |

## Step-by-step (participant)

### 1. Choose intended use

Pick one: personal prototype, live demo, publication/open-source, or clinical/production.  
This choice only shapes the **final recommendations** — every participant still walks the same path.

### 2. Testing checklist

Mark what you already do. Keep the distinction:

- **Model:** Is segmentation performance acceptable?
- **Software:** Does load → preprocess → predict/cache → save stay correct and stable?

Types to notice: smoke, unit, integration, regression, invalid-input.

### 3. Reproducibility checklist

Ideal loop:

```text
Clone → Install → Run one command → Reproduce the example result
```

Tick environment, pins, checkpoint, sample data, seed, code version, one documented command.

### 4. Run the lab

Click:

1. **Run demo** — cached MRI → overlay + Dice  
2. **Run smoke test** — output exists, shape, labels  
3. **Reproduce example** — provenance (hashes, Dice match)

If the banner says *Sample mode*, start `python scripts/tutorial_lab.py` for a live run.

### 5. Score AI-generated tests

Same task, three prompts (weak / medium / strong). For each:

1. Read the prompt and the generated test.  
2. Score yourself on the 6-point rubric (Yes/No each).  
3. **Compare with answer key** and read the critique.  
4. Optional: **Copy prompt** to reuse in your own assistant.

Rubric (0–6):

1. Calls real path  
2. Fixed example (`examples/case_001`)  
3. Observable asserts (not `assert True`)  
4. Regression anchor (`metrics.json` / hash)  
5. Failure modes (invalid inputs)  
6. Tutorial constraints (no download / GPU; CI-friendly)

Teaching point: **prompt quality drives test quality**, and even a high score still needs a real run.

### 6. Pack what you need

For Demo / Open-source / Clinical:

- Drag (or tap) evidence into the bag.  
- Leave overkill in the pool (e.g. regulatory items for a conference demo).  
- **Check my packing** for missing / overpacked feedback.

### 7. Summary

Review checklist counts, your test scores, packing scores, and “consider adding” items for your intended use.  
Educational only — **not** clinical certification.

## Facilitator notes

- Open with: *“The model already works on my laptop — what else do we need?”*  
- Live-demo the lab once; leave sample mode for rooms without installs.  
- On the weak prompt, ask: *“Would a broken pipeline still look green?”*  
- On packing: deliberately put “clinical validation” in the demo bag and discuss.  
- Close: demo-ready ≠ publication-ready ≠ clinical-ready.

## Repo map (for the activity)

| Piece | Path |
|---|---|
| Interactive site | `website/` |
| This activity guide | `docs/activity.md` · `website/activity.html` |
| Vibe-coding recipes | `docs/vibe_coding_recipes.md` |
| Prompt gallery | `examples/prompt_gallery/` |
| Lab server | `scripts/tutorial_lab.py` |
| Real tests | `tests/` |
| Cached case | `examples/case_001/` |

## What this activity is not

- Not an nnU-Net training tutorial  
- Not a claim of SOTA segmentation  
- Not regulatory or clinical certification guidance  

## Optional deeper dive (after the session)

```bash
python scripts/demo.py
python scripts/run_tests.py
python scripts/reproduce_example.py
```

Read [`docs/vibe_coding_recipes.md`](vibe_coding_recipes.md) for copy-paste prompts and acceptance checks.

Full session script: [`docs/activity.md`](activity.md) · site: [`website/activity.html`](../website/activity.html).
