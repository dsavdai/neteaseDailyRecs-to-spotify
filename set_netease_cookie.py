#!/usr/bin/env python3
"""Securely add the NetEase cookie to the ignored local env file."""

import getpass

from setup import save_netease_cookie


def main() -> int:
    while True:
        cookie = getpass.getpass(
            "Paste the complete NetEase Cookie (input hidden; Enter cancels): "
        ).strip()
        if not cookie:
            print("No cookie was saved.")
            return 1
        try:
            save_netease_cookie(cookie)
        except ValueError:
            print(
                "Cookie does not contain __csrf=. Copy the complete value from "
                "Network > Request Headers > Cookie and try again."
            )
            continue
        print("NetEase Cookie saved. No secret value was displayed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
