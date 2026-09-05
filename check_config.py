#!/usr/bin/env python3
"""Check local configuration without displaying any secret values."""

import os
import re

from dotenv import load_dotenv

from src.config import PROJECT_ROOT, REQUIRED_ENV_VARS


def main() -> int:
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path, override=False)

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    invalid = []

    playlist_id = os.getenv("SPOTIFY_PLAYLIST_ID", "")
    if playlist_id and not re.fullmatch(r"[A-Za-z0-9]+", playlist_id):
        invalid.append("SPOTIFY_PLAYLIST_ID must be a playlist ID, not a URL")

    netease_cookie = os.getenv("NETEASE_COOKIE", "")
    if netease_cookie and "__csrf=" not in netease_cookie:
        invalid.append("NETEASE_COOKIE does not contain __csrf")

    print(f"Local env file: {env_path}")
    for name in REQUIRED_ENV_VARS:
        print(f"{name}: {'SET' if os.getenv(name) else 'MISSING'}")

    if missing or invalid:
        if missing:
            print("Missing variables: " + ", ".join(missing))
        for message in invalid:
            print("Invalid configuration: " + message)
        print("Configuration is not ready. No secret values were displayed.")
        return 1

    print("Configuration shape looks ready. No secret values were displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
