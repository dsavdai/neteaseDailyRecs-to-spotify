"""Run the sync at most once per local day, after 06:00."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
STATE_DIR = Path.home() / "Library" / "Application Support" / "netease-to-spotify"
LAST_SUCCESS_FILE = STATE_DIR / "last-success-date.txt"


def main() -> int:
    now = datetime.now().astimezone()

    if now.hour < 6:
        print("Daily sync deferred until 06:00 local time.")
        return 0

    today = now.date().isoformat()
    if LAST_SUCCESS_FILE.exists():
        last_success = LAST_SUCCESS_FILE.read_text(encoding="utf-8").strip()
        if last_success == today:
            print(f"Daily sync already completed for {today}.")
            return 0

    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        print("Daily sync failed; it will be retried automatically.")
        return result.returncode

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = LAST_SUCCESS_FILE.with_suffix(".tmp")
    temporary_file.write_text(f"{today}\n", encoding="utf-8")
    temporary_file.replace(LAST_SUCCESS_FILE)
    print(f"Daily sync completed for {today}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
