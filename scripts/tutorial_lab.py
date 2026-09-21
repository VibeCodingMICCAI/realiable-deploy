#!/usr/bin/env python
"""Lightweight local tutorial lab: serve the website and run cached demo/smoke/reproduce."""

from __future__ import annotations

import json
import shutil
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
OUTPUTS = ROOT / "outputs" / "lab"
CASE = ROOT / "examples" / "case_001"


def _json_response(handler: SimpleHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _run_demo() -> dict:
    from vibe_to_trust.inference import run_cached_pipeline
    from vibe_to_trust.visualisation import save_mid_slice_overlay
    from vibe_to_trust.preprocessing import load_mri
    import nibabel as nib
    import numpy as np

    out = OUTPUTS / "demo"
    if out.exists():
        shutil.rmtree(out)
    result = run_cached_pipeline(CASE, out)
    image, _ = load_mri(next((CASE / "input").glob("*_mri.nii.gz")))
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    gt = np.asanyarray(nib.load(next((CASE / "ground_truth").glob("*_gt.nii.gz"))).dataobj)
    overlay = save_mid_slice_overlay(image, pred, out / "overlay.png", gt)
    # Copy into website assets so the static handler can show it easily.
    assets = WEBSITE / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    lab_overlay = assets / "lab_last_overlay.png"
    shutil.copy2(overlay, lab_overlay)
    metrics = result.get("metrics", {})
    return {
        "ok": True,
        "action": "demo",
        "mode": "live",
        "command": "python scripts/demo.py --no-open",
        "message": "Cached demo finished.",
        "mean_dice": metrics.get("mean_dice") or metrics.get("tutorial_resolution_dice", {}).get("mean_dice"),
        "metrics": metrics.get("tutorial_resolution_dice", metrics),
        "overlay_url": "assets/lab_last_overlay.png",
        "output": result["output"],
    }


def _run_smoke() -> dict:
    from vibe_to_trust.inference import run_cached_pipeline
    from vibe_to_trust.preprocessing import validate_segmentation
    import nibabel as nib
    import numpy as np

    out = OUTPUTS / "smoke"
    if out.exists():
        shutil.rmtree(out)
    result = run_cached_pipeline(CASE, out)
    checks = []
    ok = True

    def check(name: str, condition: bool, detail: str) -> None:
        nonlocal ok
        checks.append({"name": name, "pass": condition, "detail": detail})
        if not condition:
            ok = False

    check("output_exists", Path(result["output"]).is_file(), result["output"])
    check("mode_cached", result.get("mode") == "cached", str(result.get("mode")))
    check("shape_64", result.get("shape") == [64, 64, 64], str(result.get("shape")))
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    try:
        validate_segmentation(pred)
        check("valid_labels", True, "labels look valid")
    except Exception as exc:  # noqa: BLE001
        check("valid_labels", False, str(exc))

    return {
        "ok": ok,
        "action": "smoke",
        "mode": "live",
        "command": "python -m pytest tests/test_smoke.py -q",
        "message": "Smoke checks passed." if ok else "Smoke checks failed.",
        "checks": checks,
    }


def _run_reproduce() -> dict:
    import contextlib
    import io

    from vibe_to_trust.cli import reproduce_main

    out = OUTPUTS / "reproduce"
    if out.exists():
        shutil.rmtree(out)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = reproduce_main(["--case", str(CASE), "--out", str(out)])
    provenance_path = out / "provenance.json"
    record = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
    return {
        "ok": code == 0,
        "action": "reproduce",
        "mode": "live",
        "command": "python scripts/reproduce_example.py",
        "message": "Reproduction matched cached Dice." if code == 0 else "Reproduction mismatch.",
        "provenance": {
            "measured_mean_dice": record.get("measured_mean_dice"),
            "dice_matches_cached": record.get("dice_matches_cached"),
            "git_commit": record.get("git_commit"),
            "input_sha256": (record.get("input_sha256") or "")[:12],
            "output_sha256": (record.get("output_file_sha256") or record.get("output_array_sha256") or "")[:12],
            "tool_version": record.get("tool_version"),
        },
        "provenance_path": str(provenance_path),
    }


ACTIONS = {
    "demo": _run_demo,
    "smoke": _run_smoke,
    "reproduce": _run_reproduce,
}


class LabHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBSITE), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print("[%s] %s" % (self.log_date_time_string(), format % args))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            _json_response(self, {"ok": True, "mode": "live", "case": "examples/case_001"})
            return
        if parsed.path.startswith("/outputs/"):
            # Optional: serve lab outputs from repo root
            rel = parsed.path[len("/outputs/") :]
            target = (OUTPUTS.parent / rel).resolve()
            if str(target).startswith(str((ROOT / "outputs").resolve())) and target.is_file():
                self.path = "/"  # unused
                self.send_response(200)
                ctype = "image/png" if target.suffix == ".png" else "application/octet-stream"
                data = target.read_bytes()
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            _json_response(self, {"ok": False, "error": "not found"}, 404)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/run/"):
            _json_response(self, {"ok": False, "error": "unknown endpoint"}, 404)
            return
        action = parsed.path[len("/api/run/") :].strip("/")
        if action not in ACTIONS:
            _json_response(self, {"ok": False, "error": f"action not allowed: {action}"}, 400)
            return
        # Drain body if any
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length:
            self.rfile.read(length)
        try:
            payload = ACTIONS[action]()
            _json_response(self, payload, 200 if payload.get("ok") else 500)
        except Exception as exc:  # noqa: BLE001
            _json_response(
                self,
                {
                    "ok": False,
                    "action": action,
                    "mode": "live",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
                500,
            )


def main() -> int:
    import argparse
    import webbrowser

    parser = argparse.ArgumentParser(description="Serve the interactive tutorial lab")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), LabHandler)
    url = f"http://{args.host}:{args.port}"
    print()
    print("Tutorial lab running")
    print(f"  Open:  {url}")
    print("  API:   GET  /api/health")
    print("         POST /api/run/demo | smoke | reproduce")
    print("  Stop:  Ctrl+C")
    print()
    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLab stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
