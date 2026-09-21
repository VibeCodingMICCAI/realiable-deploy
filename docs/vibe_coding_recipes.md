# Vibe coding recipes: tests & reproducibility

How to use an AI coding assistant to **generate** software tests and a
reproduction script — and how to **judge** whether those artifacts are trustworthy.

```text
Working prototype
        ↓
Better prompts → better tests
        ↓
You score the generated tests
        ↓
Run them (lab / pytest)
        ↓
Reproduce + provenance
```

## Interactive lab

```bash
python -m pip install -e ".[test]"
python scripts/tutorial_lab.py
```

Open `http://127.0.0.1:8000` and walk through:

1. checklists  
2. **Run the lab** (demo / smoke / reproduce)  
3. **Score AI-generated tests** (weak / medium / strong prompts)  
4. pack evidence by intended use  

On plain GitHub Pages (no Python), lab buttons show pre-recorded samples and
prompt you to start `tutorial_lab.py` for a live run.

## Prompt quality matters

| Prompt | Typical result |
|---|---|
| “Write some tests for my AI model.” | `assert True`, random arrays, false green |
| “Write pytest for `run_cached_pipeline`.” | Runs the pipeline but often no Dice anchor |
| Strong prompt (path + metrics + no GPU) | Smoke + regression close to `tests/` |

Curated examples live in [`examples/prompt_gallery/`](../examples/prompt_gallery/).
They are **not** collected by CI pytest.

### Strong prompt (copy/paste)

```text
I have a cached knee MRI pipeline: run_cached_pipeline(case_dir, out_dir).
Please write pytest that:
1) smoke-runs examples/case_001 and asserts output exists, shape matches, mode=="cached";
2) regression: mean Dice vs examples/case_001/metrics.json within 1e-5;
3) does NOT download models or require GPU.
If I later change the output, regression must fail.
```

## Rubric (score 0–6 yourself)

1. Calls real path (`run_cached_pipeline` / project API)  
2. Fixed example (`examples/case_001`)  
3. Observable asserts (not `assert True`)  
4. Regression anchor (`metrics.json` / hash)  
5. Failure modes (invalid inputs)  
6. Tutorial constraints (no download, no GPU, CI-friendly)  

In the website, score each generated test, then **Compare with answer key**.

## Human acceptance checklist

- Does the test call your real code path?
- Is it bound to a fixed sample?
- Would a silent metric drop turn the test red?
- Does reproduce write shareable provenance (not only “success”)?
- Can CI run the same command?

## Map to this repository

| Artifact | Location |
|---|---|
| Smoke / integration | `tests/test_smoke.py` |
| Regression | `tests/test_regression.py` |
| Invalid input | `tests/test_invalid_inputs.py` |
| Reproduce | `scripts/reproduce_example.py` |
| Provenance helper | `src/vibe_to_trust/provenance.py` |
| Prompt gallery | `examples/prompt_gallery/` |
| Lab server | `scripts/tutorial_lab.py` |

## Teaching note

A high rubric score still needs a real run. Vibe-coded tests can look convincing
and still miss regressions. Clinical readiness needs far more than software tests.
