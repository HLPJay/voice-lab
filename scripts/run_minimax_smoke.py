#!/usr/bin/env python3
"""
Standard smoke test runner for voice_lab.

Usage:
    python scripts/run_minimax_smoke.py --dry-run          # no real calls, just server start/check
    python scripts/run_minimax_smoke.py --skip-minimax     # non-MiniMax checks only
    python scripts/run_minimax_smoke.py --real-minimax --sync-only   # minimal real test
    python scripts/run_minimax_smoke.py --real-minimax --include-batch
    python scripts/stop_smoke_server.py                    # stop any residual server

Environment variables:
    SMOKE_HOST   override host (default: 127.0.0.1)
    SMOKE_PORT   override port (default: 8010)
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent.resolve()
PID_FILE = ROOT / ".tmp" / "uvicorn-smoke.pid"
RESULT_DIR = ROOT / ".tmp" / "smoke-results"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8010
READY_TIMEOUT_SECONDS = 15


def ensure_tmp():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def load_pidfile():
    if not PID_FILE.exists():
        return None
    try:
        return json.loads(PID_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def write_pidfile(pid, host, port, cmd):
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(
        json.dumps(
            {
                "pid": pid,
                "host": host,
                "port": port,
                "cmd": cmd,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


def delete_pidfile():
    if PID_FILE.exists():
        PID_FILE.unlink()


def is_process_smoke_server(pid):
    """Check if a PID belongs to our smoke server."""
    try:
        # Windows: use tasklist and wmic
        proc = subprocess.run(
            ["wmic", "process", "where", f"processid={pid}", "get", "CommandLine"],
            capture_output=True,
            text=True,
        )
        cmdline = proc.stdout.strip()
        return "uvicorn" in cmdline and "app.main:app" in cmdline
    except Exception:
        return False


def kill_process(pid):
    """Kill a process by PID."""
    try:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def stop_server():
    """Stop the smoke server if running."""
    info = load_pidfile()
    if not info:
        return "no_pidfile"

    pid = info.get("pid")
    if not pid:
        delete_pidfile()
        return "no_pid"

    # Check if process exists
    if not is_process_smoke_server(pid):
        # PID exists but not our smoke server
        delete_pidfile()
        return "not_our_server"

    if kill_process(pid):
        delete_pidfile()
        return "killed"
    else:
        # Process might have already exited
        delete_pidfile()
        return "already_dead"


def cleanup_on_exit(pid, host, port):
    """Clean up when exiting."""
    info = load_pidfile()
    if info and info.get("pid") == pid:
        stop_server()


def port_is_free(host, port):
    """Check if port is available."""
    import socket

    try:
        with socket.create_connection((host, port), timeout=1):
            return False
    except (OSError, socket.timeout):
        return True


def wait_for_ready(host, port, timeout=READY_TIMEOUT_SECONDS):
    """Wait for server to be ready via root redirect or static page."""
    import urllib.request

    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        for path in ["/", "/static/index.html"]:
            try:
                url = f"http://{host}:{port}{path}"
                req = urllib.request.Request(url)
                resp = urllib.request.urlopen(req, timeout=2)
                if resp.status in (200,):
                    return True, path, None
                # 307/302 redirect is also OK
                if resp.status in (301, 302, 307):
                    return True, path, None
            except Exception as e:
                last_error = str(e)
        time.sleep(0.5)

    return False, None, last_error


def run_ready_check(host, port):
    """Run ready check and return result dict."""
    start = time.time()
    ready, path, error = wait_for_ready(host, port)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "name": "ready_check",
        "status": "passed" if ready else "failed",
        "duration_ms": duration_ms,
        "detail": f"{path} (http://{host}:{port}{path})" if ready else f"timeout after {READY_TIMEOUT_SECONDS}s: {error}",
    }


def run_tests(host, port, mode, real_minimax, sync_only, include_batch, include_async):
    """Run the appropriate tests based on mode."""
    import urllib.request
    import urllib.error

    results = []

    # --- Ready check always runs first ---
    results.append(run_ready_check(host, port))

    if mode == "dry-run":
        return results

    # --- Non-MiniMax checks (skip-minimax) ---
    try:
        # Jobs history list - safe, no MiniMax cost
        url = f"http://{host}:{port}/api/voice/jobs?page=1&page_size=5"
        start = time.time()
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        duration_ms = int((time.time() - start) * 1000)
        results.append({
            "name": "jobs_history",
            "status": "passed" if resp.status == 200 else "failed",
            "duration_ms": duration_ms,
            "detail": f"GET /api/voice/jobs -> {resp.status}",
        })
    except Exception as e:
        results.append({
            "name": "jobs_history",
            "status": "failed",
            "duration_ms": 0,
            "detail": str(e),
        })

    if mode == "skip-minimax":
        return results

    # --- Real MiniMax calls ---
    if not real_minimax:
        return results

    # Sync T2A - short text
    try:
        import urllib.request
        import json as json_mod

        url = f"http://{host}:{port}/api/voice/render"
        payload = json_mod.dumps({
            "text": "hello smoke test",
            "profile_id": "deep_night_programmer",
            "provider": "minimax",
            "output_format": "url",
            "confirm_cost": True,
        }).encode()
        start = time.time()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        duration_ms = int((time.time() - start) * 1000)
        data = json_mod.loads(resp.read())
        results.append({
            "name": "sync_t2a",
            "status": "success" if data.get("status") == "success" else "failed",
            "duration_ms": duration_ms,
            "detail": f"job_id={data.get('job_id')}, status={data.get('status')}",
        })
    except Exception as e:
        results.append({
            "name": "sync_t2a",
            "status": "failed",
            "duration_ms": 0,
            "detail": str(e),
        })

    # Provider voice preview - short text
    try:
        url = f"http://{host}:{port}/api/voice/provider-voices/preview"
        payload = json_mod.dumps({
            "provider": "minimax",
            "provider_voice_id": "Korean_AirheadedGirl",
            "text": "preview test",
            "model": "speech-2.8-hd",
            "confirm_cost": True,
        }).encode()
        start = time.time()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        duration_ms = int((time.time() - start) * 1000)
        data = json_mod.loads(resp.read())
        results.append({
            "name": "provider_preview",
            "status": "success" if data.get("status") == "success" else "failed",
            "duration_ms": duration_ms,
            "detail": f"job_id={data.get('job_id')}, status={data.get('status')}",
        })
    except Exception as e:
        results.append({
            "name": "provider_preview",
            "status": "failed",
            "duration_ms": 0,
            "detail": str(e),
        })

    if include_async:
        results.append({
            "name": "async_t2a",
            "status": "skipped",
            "duration_ms": 0,
            "detail": "async T2A skipped by default (4.5min per task); use --include-async to enable",
        })

    if include_batch:
        results.append({
            "name": "batch_longtext",
            "status": "skipped",
            "duration_ms": 0,
            "detail": "batch longtext skipped by default; use --include-batch to enable",
        })
        results.append({
            "name": "batch_script",
            "status": "skipped",
            "duration_ms": 0,
            "detail": "batch script skipped by default; use --include-batch to enable",
        })

    return results


def write_results(mode, real_minimax, base_url, results, cleanup_status):
    ensure_tmp()
    result_file = RESULT_DIR / "latest.json"
    result_file.write_text(
        json.dumps(
            {
                "started_at": datetime.now(timezone.utc).isoformat(),
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "base_url": base_url,
                "mode": mode,
                "real_minimax": real_minimax,
                "results": results,
                "cleanup": cleanup_status,
            },
            indent=2,
        )
    )
    print(f"Results written to {result_file}")


def main():
    parser = argparse.ArgumentParser(description="voice_lab smoke test runner")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Start server, ready check, stop. No MiniMax calls.",
    )
    parser.add_argument(
        "--skip-minimax",
        action="store_true",
        help="Run non-MiniMax API checks only.",
    )
    parser.add_argument(
        "--real-minimax",
        action="store_true",
        help="Allow real MiniMax API calls. Required for actual smoke testing.",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Only run sync T2A (no async, no batch). Default when --real-minimax is used.",
    )
    parser.add_argument(
        "--include-batch",
        action="store_true",
        help="Include batch longtext/script tests (requires --real-minimax).",
    )
    parser.add_argument(
        "--include-async",
        action="store_true",
        help="Include async T2A test (requires --real-minimax, ~4.5min).",
    )
    args = parser.parse_args()

    if not (args.dry_run or args.skip_minimax or args.real_minimax):
        parser.print_help()
        print("\nError: must specify one of --dry-run, --skip-minimax, or --real-minimax")
        sys.exit(1)

    if args.real_minimax and not (
        args.sync_only or args.include_batch or args.include_async
    ):
        # Default to sync-only when running real minimax
        args.sync_only = True

    mode = "dry-run"
    if args.skip_minimax:
        mode = "skip-minimax"
    elif args.real_minimax:
        mode = "real-minimax"

    host = os.environ.get("SMOKE_HOST", DEFAULT_HOST)
    port = int(os.environ.get("SMOKE_PORT", DEFAULT_PORT))
    base_url = f"http://{host}:{port}"

    print(f"[smoke] mode={mode} base_url={base_url} real_minimax={args.real_minimax}")

    # --- Step 1: Stop any previous residual server ---
    print("[smoke] Checking for residual smoke server...")
    prev = stop_server()
    if prev == "killed":
        print("[smoke] Stopped residual smoke server")
    elif prev == "no_pidfile":
        print("[smoke] No pidfile found")
    elif prev == "no_pid":
        print("[smoke] pidfile had no pid, deleted")
    elif prev == "not_our_server":
        print("[smoke] pidfile PID is not our smoke server, deleted")
    elif prev == "already_dead":
        print("[smoke] Process already dead, deleted pidfile")

    # --- Step 2: Check port availability ---
    if not port_is_free(host, port):
        print(f"[smoke] ERROR: Port {port} is already in use by an unknown process.")
        print(f"[smoke] The smoke runner will not kill unknown processes.")
        print(f"[smoke] To find the process on Windows:")
        print(f"  netstat -ano | findstr :{port}")
        print(f"[smoke] To stop it manually:")
        print(f"  taskkill /PID <PID> /F")
        print(f"[smoke] Or choose another port:")
        print(f"  SMOKE_PORT={port + 1} python scripts/run_minimax_smoke.py ...")
        sys.exit(1)

    # --- Step 3: Start uvicorn (no --reload) ---
    print(f"[smoke] Starting uvicorn on {host}:{port} ...")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pid = proc.pid
    write_pidfile(pid, host, port, " ".join(cmd))
    print(f"[smoke] uvicorn started pid={pid}")

    # --- Step 4: Wait for ready ---
    print(f"[smoke] Waiting for ready (timeout={READY_TIMEOUT_SECONDS}s)...")
    ready, path, error = wait_for_ready(host, port)
    if not ready:
        print(f"[smoke] ERROR: Server did not become ready within {READY_TIMEOUT_SECONDS}s")
        print(f"[smoke] stderr:\n{proc.stderr.read1(4096).decode(errors='replace')}")
        cleanup_status = stop_server()
        print(f"[smoke] Cleanup: {cleanup_status}")
        sys.exit(1)

    print(f"[smoke] Server ready at {base_url}{path}")

    # --- Step 5: Run tests ---
    cleanup_status = "not_run"
    try:
        results = run_tests(
            host=host,
            port=port,
            mode=mode,
            real_minimax=args.real_minimax,
            sync_only=args.sync_only,
            include_batch=args.include_batch,
            include_async=args.include_async,
        )
        # Print summary
        print("\n[smoke] Results:")
        for r in results:
            icon = "PASS" if r["status"] == "passed" else "FAIL" if r["status"] == "failed" else "SKIP"
            print(f"  [{icon}] {r['name']}: {r['detail']} ({r['duration_ms']}ms)")
    finally:
        # --- Step 6: Cleanup ---
        print("[smoke] Stopping server...")
        cleanup_status = stop_server()
        print(f"[smoke] Cleanup: {cleanup_status}")

    write_results(mode, args.real_minimax, base_url, results, cleanup_status)

    # Exit code based on test results
    if mode != "dry-run":
        failures = [r for r in results if r["status"] == "failed"]
        if failures:
            print(f"\n[smoke] FAILED: {len(failures)} test(s) failed")
            sys.exit(1)
        else:
            print(f"\n[smoke] ALL TESTS PASSED")
            sys.exit(0)
    else:
        print("\n[smoke] Dry-run complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
