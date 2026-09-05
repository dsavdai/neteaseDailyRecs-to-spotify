#!/usr/bin/env python3
"""Import a NetEase cookie from the macOS clipboard without displaying it."""

import subprocess

from setup import save_netease_cookie


def main() -> int:
    result = subprocess.run(
        ["pbpaste"],
        check=True,
        capture_output=True,
        text=True,
    )
    cookie = result.stdout.strip()
    if not cookie:
        print("Clipboard is empty. No Cookie was saved.")
        return 1
    try:
        save_netease_cookie(cookie)
    except ValueError:
        print(
            "Clipboard does not contain a complete NetEase Cookie with __csrf=. "
            "Copy Request Headers > Cookie value and try again."
        )
        return 1
    print("NetEase Cookie imported from clipboard without displaying its value.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
