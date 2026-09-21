# Vibe coding recipes

## Core regression prompt (stale reuse)

```text
Inspect the result-reuse logic. Add a regression test that processes two controlled
cases with different reference predictions sequentially in the same output directory.
Snapshot the first saved output before the second call, then verify each result matches
its own reference. Demonstrate failure on the faulty reuse policy before fixing it.
Do not modify reference predictions or examples/case_001.
```

Minimal fix taught on the stand: **always process the current input and overwrite**.
Safe caching (content hash + model id + config) is optional advanced discussion only.

## Stages

1. Inspect contract before editing.  
2. Implement focused test + fix.  
3. Review diff; separate executed vs proposed checks.

Canonical UI strings also live in `website/assets/tutorial_content.json` / `script.js`.
