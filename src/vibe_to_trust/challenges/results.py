"""Challenge result helpers."""

from __future__ import annotations

from typing import Any


def check(
    name: str,
    passed: bool,
    *,
    expected: Any = None,
    observed: Any = None,
    detail: str = "",
) -> dict:
    return {
        "name": name,
        "pass": bool(passed),
        "expected": expected,
        "observed": observed,
        "detail": detail,
    }


def bundle(
    *,
    challenge_id: str,
    title: str,
    command: str,
    checks: list[dict],
    explanation: str,
    mode: str = "live",
    meta: dict | None = None,
) -> dict:
    ok = all(c["pass"] for c in checks) if checks else False
    return {
        "ok": ok,
        "action": challenge_id,
        "challenge_id": challenge_id,
        "title": title,
        "mode": mode,
        "command": command,
        "message": "All listed checks passed." if ok else "One or more listed checks failed.",
        "checks": checks,
        "explanation": explanation,
        "meta": meta or {},
    }
