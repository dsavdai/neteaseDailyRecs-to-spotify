# Local setup checklist

The repository is ready locally. Keep all credentials in the ignored `.env`
file and never commit or paste them into chat, issues, or logs.

## 1. Spotify app and private playlist

1. Create an app at <https://developer.spotify.com/dashboard>.
2. Add this exact Redirect URI in the app settings:
   `http://127.0.0.1:8888/callback`
3. Create a dedicated **private** Spotify playlist. The setup helper requests
   the least-privilege `playlist-modify-private` scope.
4. Spotify Development Mode app owners currently need Spotify Premium.

Run the interactive authorization helper locally:

```bash
.venv/bin/python setup.py
```

Enter the Client ID, Client Secret, and private playlist URL/ID only in that
local prompt. The helper opens the Spotify authorization page and receives the
`127.0.0.1` callback automatically. It then obtains the refresh token and
stores all Spotify values in the ignored local `.env` file without displaying
them. If the local callback port is unavailable, the original manual-copy
fallback remains available.

## 2. NetEase cookie

Sign in at <https://music.163.com/> in your browser. Open Developer Tools and
copy the complete cookie value for requests to `music.163.com` from either:

- Application > Storage > Cookies > `https://music.163.com`, or
- Network > a request to `music.163.com` > Request Headers > Cookie.

Copy the value only, without the `Cookie:` label. It must contain `__csrf=`.
Treat the full cookie as a password; replace it when the login session expires.

## 3. Fill `.env`

Open the ignored `.env` file and fill these five values:

```dotenv
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REFRESH_TOKEN=
SPOTIFY_PLAYLIST_ID=
NETEASE_COOKIE=
```

Use only the playlist ID for `SPOTIFY_PLAYLIST_ID`, not the full URL.

Check the configuration without printing secret values:

```bash
.venv/bin/python check_config.py
```

Run the read-only end-to-end test first:

```bash
.venv/bin/python -m src.dry_run
```

Only after reviewing `match_report.json`, run the write operation if desired:

```bash
.venv/bin/python -m src.main
```

The write operation replaces the current playlist contents. Use a dedicated
playlist.

## 4. macOS daily automation

Install the per-user LaunchAgent after the first successful sync:

```bash
.venv/bin/python automation.py install
```

It checks every 30 minutes and succeeds at most once per local day after
06:00. A failed run leaves the prior playlist intact and is retried later.

Inspect or remove it with:

```bash
.venv/bin/python automation.py status
.venv/bin/python automation.py uninstall
```

## 5. GitHub Actions

Fork the upstream repository, push these local changes to the fork, then add
the same five names under repository Settings > Secrets and variables > Actions.
Run `NetEase Spotify Match Dry Run` manually before running
`Sync NetEase Daily Recommendations`.

The scheduled workflow uses `0 22 * * *`: every day at 22:00 UTC, which is
06:00 the next day in Asia/Shanghai. GitHub schedules can be delayed, and a
scheduled workflow must exist on the default branch.
