#!/usr/bin/env python3
"""
Stop any residual smoke server.

Reads .tmp/uvicorn-smoke.pid, verifies the process is our smoke server
(uvicorn + app.main:app), and stops it. Deletes the pidfile afterward.

Usage:
    python scripts/stop_smoke_server.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
PID_FILE = ROOT / ".tmp" / "uvicorn-smoke.pid"


def is_process_smoke_server(pid):
    """Check if PID belongs to our smoke server (uvicorn + app.main:app)."""
    try:
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


def main():
    if not PID_FILE.exists():
        print("stop_smoke: no pidfile found, nothing to stop")
        sys.exit(0)

    try:
        info = json.loads(PID_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        print("stop_smoke: pidfile corrupted, deleting")
        PID_FILE.unlink()
        sys.exit(0)

    pid = info.get("pid")
    if not pid:
        print("stop_smoke: pidfile has no pid, deleting")
        PID_FILE.unlink()
        sys.exit(0)

    if not is_process_smoke_server(pid):
        if is_process_alive(pid):
            print(f"stop_smoke: pid {pid} exists but is not a smoke server, not killing")
            print(f"stop_smoke: command line check: {get_commandline(pid)}")
            sys.exit(1)
        else:
            print(f"stop_smoke: pid {pid} is not running, deleting pidfile")
            PID_FILE.unlink()
            sys.exit(0)

    if kill_process(pid):
        print(f"stop_smoke: killed pid {pid}")
        PID_FILE.unlink()
        print("stop_smoke: pidfile deleted")
        sys.exit(0)
    else:
        print(f"stop_smoke: kill failed for pid {pid}, process may have already exited")
        PID_FILE.unlink()
        sys.exit(0)


def is_process_alive(pid):
    """Check if a process exists."""
    try:
        subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_commandline(pid):
    """Get command line of a process."""
    try:
        proc = subprocess.run(
            ["wmic", "process", "where", f"processid={pid}", "get", "CommandLine"],
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "(unknown)"


if __name__ == "__main__":
    main()
