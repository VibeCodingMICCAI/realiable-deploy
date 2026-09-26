#!/usr/bin/env python
"""Lightweight local tutorial lab: website + allowlisted demo/challenge APIs."""

from __future__ import annotations

import json
import shutil
import tempfile
import traceback
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
OUTPUTS = ROOT / "outputs" / "lab"
CASE = ROOT / "examples" / "case_001"


def _json_response(handler: SimpleHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, indent=2, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _session_dir() -> Path:
    path = OUTPUTS / "sessions" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _run_demo() -> dict:
    from vibe_to_trust.inference import run_cached_pipeline
    from vibe_to_trust.visualisation import save_mid_slice_overlay
    from vibe_to_trust.preprocessing import load_mri
    import nibabel as nib
    import numpy as np

    out = _session_dir() / "demo"
    result = run_cached_pipeline(CASE, out)
    image, _ = load_mri(next((CASE / "input").glob("*_mri.nii.gz")))
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    gt = np.asanyarray(nib.load(next((CASE / "ground_truth").glob("*_gt.nii.gz"))).dataobj)
    overlay = save_mid_slice_overlay(image, pred, out / "overlay.png", gt)
    assets = WEBSITE / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    lab_overlay = assets / "lab_last_overlay.png"
    shutil.copy2(overlay, lab_overlay)
    metrics = result.get("metrics", {})
    return {
        "ok": True,
        "action": "demo",
        "mode": "live",
        "command": "vibe_to_trust.inference.run_cached_pipeline(examples/case_001)",
        "message": "Cached demo finished (software path on packaged extract).",
        "mean_dice": metrics.get("mean_dice"),
        "metrics": metrics,
        "overlay_url": "assets/lab_last_overlay.png",
        "output": result["output"],
        "checks": [
            {"name": "output_exists", "pass": True, "expected": True, "observed": True, "detail": result["output"]},
            {
                "name": "mode_cached",
                "pass": result.get("mode") == "cached",
                "expected": "cached",
                "observed": result.get("mode"),
                "detail": "",
            },
        ],
        "explanation": "Cached tutorial extract only — not full-resolution model validation.",
    }


def _run_smoke() -> dict:
    from vibe_to_trust.inference import run_cached_pipeline
    from vibe_to_trust.preprocessing import validate_segmentation
    import nibabel as nib
    import numpy as np

    out = _session_dir() / "smoke"
    result = run_cached_pipeline(CASE, out)
    checks = []
    ok = True

    def add(name: str, condition: bool, expected, observed, detail: str = "") -> None:
        nonlocal ok
        checks.append(
            {"name": name, "pass": condition, "expected": expected, "observed": observed, "detail": detail}
        )
        if not condition:
            ok = False

    add("output_exists", Path(result["output"]).is_file(), True, Path(result["output"]).is_file(), result["output"])
    add("mode_cached", result.get("mode") == "cached", "cached", result.get("mode"))
    add("shape_64", result.get("shape") == [64, 64, 64], [64, 64, 64], result.get("shape"))
    pred = np.asanyarray(nib.load(result["output"]).dataobj)
    try:
        validate_segmentation(pred)
        add("valid_labels", True, "labels in {0..5}", "ok")
    except Exception as exc:  # noqa: BLE001
        add("valid_labels", False, "labels in {0..5}", str(exc))

    return {
        "ok": ok,
        "action": "smoke",
        "mode": "live",
        "command": "run_cached_pipeline + validate_segmentation (packaged case_001)",
        "message": "Smoke checks passed." if ok else "Smoke checks failed.",
        "checks": checks,
        "explanation": "Smoke covers the packaged cached path, not optional real nnU-Net inference.",
    }


def _run_reproduce() -> dict:
    import contextlib
    import io
    from vibe_to_trust.cli import reproduce_main

    out = _session_dir() / "reproduce"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = reproduce_main(["--case", str(CASE), "--out", str(out)])
    provenance_path = out / "provenance.json"
    record = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
    return {
        "ok": code == 0,
        "action": "reproduce",
        "mode": "live",
        "command": "vibe_to_trust.cli.reproduce_main(--case examples/case_001)",
        "message": "Reproduction matched cached Dice." if code == 0 else "Reproduction mismatch.",
        "checks": [
            {
                "name": "dice_matches_cached",
                "pass": bool(record.get("dice_matches_cached")),
                "expected": True,
                "observed": record.get("dice_matches_cached"),
                "detail": f"measured={record.get('measured_mean_dice')}",
            }
        ],
        "provenance": {
            "measured_mean_dice": record.get("measured_mean_dice"),
            "dice_matches_cached": record.get("dice_matches_cached"),
            "git_commit": record.get("git_commit"),
            "input_sha256": (record.get("input_sha256") or "")[:12],
            "output_sha256": (record.get("output_file_sha256") or record.get("output_array_sha256") or "")[:12],
            "tool_version": record.get("tool_version"),
        },
        "provenance_path": str(provenance_path),
        "explanation": "Reproducing the cached extract verifies the software path, not clinical performance.",
    }


def _run_challenge(challenge_id: str, body: dict | None = None) -> dict:
    from vibe_to_trust.challenges import ALLOWED_CHALLENGES, run_challenge
    from vibe_to_trust.challenges import stale_reuse as stale

    body = body or {}
    work = _session_dir()

    if challenge_id == "stale_reset":
        result = stale.create_exercise_session(OUTPUTS / "stale")
        result["mode"] = "live"
        result["command"] = "stale_reuse.create_exercise_session"
        return result

    if challenge_id in {"stale_process_A", "stale_process_B", "stale_compare"}:
        sid = body.get("session_id")
        if not sid:
            return {"ok": False, "error": "session_id required. Run reset first.", "mode": "live"}
        session_dir = OUTPUTS / "stale" / sid
        reuse = bool(body.get("reuse_existing", True))
        if challenge_id == "stale_compare":
            result = stale.session_compare(session_dir)
        else:
            case_id = "A" if challenge_id.endswith("A") else "B"
            result = stale.session_process(session_dir, case_id, reuse_existing=reuse)
        result["mode"] = "live"
        return result

    if challenge_id not in ALLOWED_CHALLENGES:
        return {"ok": False, "error": f"challenge not allowed: {challenge_id}", "mode": "live"}
    result = run_challenge(challenge_id, work_root=work)
    result["mode"] = "live"
    return result


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
            from vibe_to_trust.challenges import ALLOWED_CHALLENGES

            _json_response(
                self,
                {
                    "ok": True,
                    "mode": "live",
                    "case": "examples/case_001",
                    "challenges": sorted(ALLOWED_CHALLENGES),
                    "execution_note": "Live means allowlisted Python on this machine; cached demo is still cached (not fresh nnU-Net inference).",
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/run/"):
            _json_response(self, {"ok": False, "error": "unknown endpoint"}, 404)
            return
        action = parsed.path[len("/api/run/") :].strip("/")
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        body: dict = {}
        if raw:
            try:
                body = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                body = {}

        try:
            if action in ACTIONS:
                payload = ACTIONS[action]()
            elif action.startswith("challenge/"):
                challenge_id = action[len("challenge/") :]
                payload = _run_challenge(challenge_id, body)
            else:
                _json_response(self, {"ok": False, "error": f"action not allowed: {action}"}, 400)
                return
            status = 200
            if not payload.get("ok"):
                if payload.get("expected_failure") or challenge_id_from(action) in {
                    "stale_regression_faulty",
                    "affine_geometry_faulty",
                    "mean_dice_reveal",
                    "mean_dice_regression_faulty",
                    "overlay_reveal",
                    "overlay_regression_faulty",
                }:
                    status = 200
                    payload["expected_failure"] = True
                elif action.startswith("challenge/"):
                    status = 200
                else:
                    status = 500
            _json_response(self, payload, status)
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


def challenge_id_from(action: str) -> str:
    if action.startswith("challenge/"):
        return action[len("challenge/") :]
    return ""


def main() -> int:
    import argparse
    import webbrowser

    parser = argparse.ArgumentParser(description="Serve the interactive tutorial lab")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    try:
        from vibe_to_trust.challenges.stand_examples import ensure_teaching_assets

        ensure_teaching_assets(WEBSITE)
    except Exception as exc:  # noqa: BLE001
        print(f"Note: could not ensure teaching assets ({exc})")
    server = ThreadingHTTPServer((args.host, args.port), LabHandler)
    url = f"http://{args.host}:{args.port}"
    print()
    print("Tutorial lab running")
    print(f"  Open:  {url}")
    print("  API:   GET  /api/health")
    print("         POST /api/run/demo | smoke | reproduce")
    print("         POST /api/run/challenge/<id>")
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
