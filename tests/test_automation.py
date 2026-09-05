import plistlib
from pathlib import Path

from automation import LABEL, build_plist, launch_agent_path


def test_build_plist_uses_portable_user_and_project_paths():
    project = Path("/Users/example/projects/netease-to-spotify")
    home = Path("/Users/example")
    payload = plistlib.loads(build_plist(project, home))

    assert payload["Label"] == LABEL
    assert payload["ProgramArguments"] == [
        str(project / ".venv" / "bin" / "python"),
        str(project / "daily_sync.py"),
    ]
    assert payload["StartInterval"] == 1800
    assert payload["RunAtLoad"] is True
    assert payload["StandardOutPath"] == str(
        home / "Library" / "Logs" / "netease-to-spotify.log"
    )


def test_launch_agent_path_is_user_specific():
    home = Path("/Users/someone")
    assert launch_agent_path(home) == (
        home / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    )
