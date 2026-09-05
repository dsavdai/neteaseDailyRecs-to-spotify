#!/usr/bin/env python3
"""Install, inspect, or remove the macOS daily sync LaunchAgent."""

from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path


LABEL = "com.netease-to-spotify.daily-sync"
PROJECT_ROOT = Path(__file__).resolve().parent


def launch_agent_path(home: Path) -> Path:
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def build_plist(project_root: Path, home: Path) -> bytes:
    python_executable = project_root / ".venv" / "bin" / "python"
    daily_sync = project_root / "daily_sync.py"
    logs = home / "Library" / "Logs"
    payload = {
        "Label": LABEL,
        "ProgramArguments": [str(python_executable), str(daily_sync)],
        "RunAtLoad": True,
        "StartInterval": 1800,
        "StandardOutPath": str(logs / "netease-to-spotify.log"),
        "StandardErrorPath": str(logs / "netease-to-spotify-error.log"),
        "ProcessType": "Background",
    }
    return plistlib.dumps(payload, sort_keys=False)


def service_target() -> str:
    return f"gui/{os.getuid()}/{LABEL}"


def domain_target() -> str:
    return f"gui/{os.getuid()}"


def require_macos_project() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("Local automation installation currently supports macOS only.")
    if not (PROJECT_ROOT / ".venv" / "bin" / "python").exists():
        raise RuntimeError("Run configure.command first to create .venv.")
    if not (PROJECT_ROOT / ".env").exists():
        raise RuntimeError("Run configure.command first to create the local .env file.")


def install() -> None:
    require_macos_project()
    home = Path.home()
    plist_path = launch_agent_path(home)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    (home / "Library" / "Logs").mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(build_plist(PROJECT_ROOT, home))

    subprocess.run(
        ["launchctl", "bootout", domain_target(), str(plist_path)],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["launchctl", "bootstrap", domain_target(), str(plist_path)],
        check=True,
    )
    subprocess.run(
        ["launchctl", "enable", service_target()],
        check=True,
    )
    print("Daily automation installed.")
    print("It checks every 30 minutes and syncs once per day after 06:00.")


def status() -> int:
    result = subprocess.run(
        ["launchctl", "print", service_target()],
        check=False,
    )
    return result.returncode


def uninstall() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("Local automation management currently supports macOS only.")
    plist_path = launch_agent_path(Path.home())
    subprocess.run(
        ["launchctl", "bootout", domain_target(), str(plist_path)],
        check=False,
        capture_output=True,
    )
    if plist_path.exists():
        plist_path.unlink()
    print("Daily automation removed. Local credentials were kept.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "status", "uninstall"))
    args = parser.parse_args()

    if args.action == "install":
        install()
        return 0
    if args.action == "status":
        return status()
    uninstall()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
