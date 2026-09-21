#!/usr/bin/env python
"""Memorable entry points for the tutorial."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> int:
    print("$ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def setup() -> int:
    return run([sys.executable, "-m", "pip", "install", "-e", ".[test]"])


def test() -> int:
    return run([sys.executable, "-m", "pytest"])


def demo() -> int:
    return run([sys.executable, "-m", "vibe_to_trust.cli", "demo"])


def reproduce() -> int:
    return run([sys.executable, "-m", "vibe_to_trust.cli", "reproduce"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Tutorial helper commands")
    parser.add_argument("command", choices=["setup", "test", "demo", "reproduce"])
    args = parser.parse_args()
    return {"setup": setup, "test": test, "demo": demo, "reproduce": reproduce}[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
