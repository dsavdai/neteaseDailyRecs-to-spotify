import base64
import stat
from urllib.parse import parse_qs, urlparse

import pytest

import setup


def test_playlist_url_and_raw_id():
    assert setup.playlist_id_from_input("abc123") == "abc123"
    assert setup.playlist_id_from_input(
        "https://open.spotify.com/playlist/abc123"
    ) == "abc123"


def test_invalid_playlist_input():
    with pytest.raises(ValueError):
        setup.playlist_id_from_input("https://open.spotify.com/album/abc123")
    with pytest.raises(ValueError):
        setup.playlist_id_from_input("bad id")


def test_authorization_url_uses_required_scope_and_state():
    url = setup.build_authorization_url("client", "state-value")
    query = parse_qs(urlparse(url).query)
    assert query["scope"] == [setup.SPOTIFY_SCOPE]
    assert query["state"] == ["state-value"]
    assert query["redirect_uri"] == [setup.REDIRECT_URI]


def test_callback_state_validation():
    callback = (
        f"{setup.REDIRECT_URI}?code=code-value&state=state-value"
    )
    assert setup.extract_callback_code(callback, "state-value") == "code-value"
    with pytest.raises(ValueError):
        setup.extract_callback_code(callback, "wrong-state")


def test_callback_url_from_path():
    assert setup.callback_url_from_path(
        "/callback?code=code-value&state=state-value"
    ) == f"{setup.REDIRECT_URI}?code=code-value&state=state-value"
    with pytest.raises(ValueError):
        setup.callback_url_from_path("/wrong?code=code-value")


def test_token_exchange_does_not_expose_secret(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"refresh_token": "refresh-token"}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(setup.requests, "post", fake_post)
    assert setup.exchange_code("client", "secret", "code") == "refresh-token"
    assert captured["data"]["grant_type"] == "authorization_code"
    assert captured["timeout"] == 30
    assert "secret" not in str(captured.get("data", {}))


def test_save_local_env_preserves_cookie_and_restricts_permissions(
    monkeypatch, tmp_path,
):
    env_path = tmp_path / ".env"
    env_path.write_text("NETEASE_COOKIE='__csrf=existing'\n", encoding="utf-8")
    monkeypatch.setattr(setup, "PROJECT_ROOT", tmp_path)

    saved_path = setup.save_local_env(
        "client-id", "client-secret", "refresh-token", "playlist-id"
    )
    contents = saved_path.read_text(encoding="utf-8")

    assert "NETEASE_COOKIE='__csrf=existing'" in contents
    assert "SPOTIFY_CLIENT_ID='client-id'" in contents
    assert "SPOTIFY_CLIENT_SECRET='client-secret'" in contents
    assert "SPOTIFY_REFRESH_TOKEN='refresh-token'" in contents
    assert "SPOTIFY_PLAYLIST_ID='playlist-id'" in contents
    assert stat.S_IMODE(saved_path.stat().st_mode) == 0o600


def test_save_netease_cookie_validates_before_writing(monkeypatch, tmp_path):
    monkeypatch.setattr(setup, "PROJECT_ROOT", tmp_path)

    with pytest.raises(ValueError):
        setup.save_netease_cookie("MUSIC_U=only")

    saved_path = setup.save_netease_cookie("MUSIC_U=value; __csrf=token")
    contents = saved_path.read_text(encoding="utf-8")
    assert "NETEASE_COOKIE='MUSIC_U=value; __csrf=token'" in contents
    assert stat.S_IMODE(saved_path.stat().st_mode) == 0o600
