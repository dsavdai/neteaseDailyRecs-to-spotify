from pathlib import Path

from src import config


def test_load_settings_reads_project_env_without_overriding_process_env(
    monkeypatch, tmp_path: Path,
):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SPOTIFY_CLIENT_ID=file-client\n"
        "SPOTIFY_CLIENT_SECRET=file-secret\n"
        "SPOTIFY_REFRESH_TOKEN=file-refresh\n"
        "SPOTIFY_PLAYLIST_ID=file-playlist\n"
        "NETEASE_COOKIE=__csrf=file-csrf\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "process-client")
    for name in config.REQUIRED_ENV_VARS[1:]:
        monkeypatch.delenv(name, raising=False)

    settings = config.load_settings()

    assert settings.spotify_client_id == "process-client"
    assert settings.spotify_client_secret == "file-secret"
    assert settings.netease_cookie == "__csrf=file-csrf"
