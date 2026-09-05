#!/usr/bin/env python3
"""Interactive helper for creating a Spotify refresh token locally."""

import base64
import getpass
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import dotenv_values, set_key


SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SCOPE = "playlist-modify-private"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
PROJECT_ROOT = Path(__file__).resolve().parent


def playlist_id_from_input(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 2 and parts[0] == "playlist":
            value = parts[1]
        else:
            raise ValueError("Enter a Spotify playlist URL or playlist ID.")
    if not value or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" for character in value):
        raise ValueError("Enter a valid Spotify playlist URL or playlist ID.")
    return value


def build_authorization_url(client_id: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SPOTIFY_SCOPE,
        "state": state,
    }
    return f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}"


def extract_callback_code(callback: str, expected_state: str) -> str:
    parsed = urlparse(callback.strip())
    values = parse_qs(parsed.query)
    if values.get("state", [None])[0] != expected_state:
        raise ValueError("OAuth state mismatch.")
    if values.get("error", [None])[0]:
        raise ValueError(f"Spotify authorization failed: {values['error'][0]}")
    code = values.get("code", [None])[0]
    if not code:
        raise ValueError("Callback URL does not contain an authorization code.")
    return code


def callback_url_from_path(path: str) -> str:
    """Turn a local callback request path into the full configured URL."""
    parsed = urlparse(path)
    if parsed.path != "/callback":
        raise ValueError("Unexpected callback path.")
    return f"{REDIRECT_URI}?{parsed.query}"


def wait_for_callback(authorization_url: str, timeout_seconds: int = 300) -> str:
    """Open Spotify authorization and receive the loopback callback locally."""
    result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            try:
                result["url"] = callback_url_from_path(self.path)
                status = 200
                message = (
                    "Spotify authorization received. You can close this tab "
                    "and return to the terminal."
                )
            except ValueError as error:
                status = 400
                message = str(error)

            body = (
                "<!doctype html><meta charset='utf-8'>"
                f"<title>Spotify setup</title><h1>{message}</h1>"
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args) -> None:
            return

    with HTTPServer(("127.0.0.1", 8888), CallbackHandler) as server:
        server.timeout = timeout_seconds
        print("Opening Spotify authorization in your browser...")
        print("Waiting for the local callback (up to 5 minutes)...")
        if not webbrowser.open(authorization_url):
            print("The browser did not open automatically. Open this URL:")
            print(authorization_url)
        server.handle_request()

    callback_url = result.get("url")
    if not callback_url:
        raise TimeoutError("Spotify authorization timed out. Please run setup again.")
    return callback_url


def exchange_code(client_id: str, client_secret: str, code: str) -> str:
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode("utf-8")
    ).decode("ascii")
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("refresh_token")
    if not token:
        raise RuntimeError("Spotify did not return a refresh token.")
    return token


def save_local_env(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    playlist_id: str,
    netease_cookie: str = "",
) -> Path:
    """Save credentials locally without displaying them in terminal output."""
    env_path = PROJECT_ROOT / ".env"
    env_path.touch(mode=0o600, exist_ok=True)
    values = {
        "SPOTIFY_CLIENT_ID": client_id,
        "SPOTIFY_CLIENT_SECRET": client_secret,
        "SPOTIFY_REFRESH_TOKEN": refresh_token,
        "SPOTIFY_PLAYLIST_ID": playlist_id,
    }
    if netease_cookie:
        if "__csrf=" not in netease_cookie:
            raise ValueError("NetEase cookie must contain __csrf=.")
        values["NETEASE_COOKIE"] = netease_cookie
    for name, value in values.items():
        set_key(env_path, name, value, quote_mode="always")
    os.chmod(env_path, 0o600)
    return env_path


def save_netease_cookie(cookie: str) -> Path:
    """Validate and save a NetEase cookie without displaying its value."""
    if "__csrf=" not in cookie:
        raise ValueError("NetEase cookie must contain __csrf=.")
    env_path = PROJECT_ROOT / ".env"
    env_path.touch(mode=0o600, exist_ok=True)
    set_key(env_path, "NETEASE_COOKIE", cookie, quote_mode="always")
    os.chmod(env_path, 0o600)
    return env_path


def main() -> None:
    existing = dotenv_values(PROJECT_ROOT / ".env")
    client_id = str(existing.get("SPOTIFY_CLIENT_ID") or "").strip()
    if client_id:
        print("Spotify Client ID: using the saved local value.")
    else:
        client_id = input("Spotify Client ID: ").strip()
    client_secret = getpass.getpass("Spotify Client Secret: ").strip()
    playlist_input = str(existing.get("SPOTIFY_PLAYLIST_ID") or "").strip()
    if playlist_input:
        print("Private Spotify playlist: using the saved local value.")
    else:
        playlist_input = input("Private Spotify playlist URL or ID: ")
    playlist_id = playlist_id_from_input(playlist_input)

    state = secrets.token_urlsafe(24)
    authorization_url = build_authorization_url(client_id, state)
    try:
        callback = wait_for_callback(authorization_url)
    except OSError as error:
        print(f"Could not listen on 127.0.0.1:8888: {error}")
        print("Open this URL in your browser:")
        print(authorization_url)
        callback = input("Paste the full callback URL: ")
    refresh_token = exchange_code(client_id, client_secret, extract_callback_code(callback, state))
    env_path = save_local_env(
        client_id,
        client_secret,
        refresh_token,
        playlist_id,
    )

    netease_cookie = ""
    while True:
        netease_cookie = getpass.getpass(
            "NetEase cookie (input hidden; press Enter to add it later): "
        ).strip()
        if not netease_cookie:
            break
        try:
            save_netease_cookie(netease_cookie)
            break
        except ValueError:
            print(
                "Cookie was not saved because it does not contain __csrf=. "
                "Copy the complete Request Headers > Cookie value and try again, "
                "or press Enter to skip."
            )

    print("\nSetup complete.")
    print(f"Spotify credentials were saved to {env_path}.")
    print("No secret values were displayed.")
    if not netease_cookie:
        print("Add NETEASE_COOKIE to that file, then run: python check_config.py")
    else:
        print("NetEase cookie was saved without being displayed.")
    print("Later, copy the same five variables to GitHub Repository Secrets.")


if __name__ == "__main__":
    main()
