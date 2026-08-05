"""Shared fixtures for GitHub Action-style CLI tests."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

type RunChangelogAction = Callable[..., tuple[str, str, str, str]]


@pytest.fixture
def run_changelog_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> RunChangelogAction:
    """Run the Action with a changelog and inputs, returning its results."""

    def run(
        changelog_content: str, expected_exit_code: int = 0, **environment: str
    ) -> tuple[str, str, str, str]:
        monkeypatch.chdir(tmp_path)
        output_path = tmp_path / "github-output"
        monkeypatch.setenv("GITHUB_REPOSITORY", "acme/widget")
        monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
        for name in (
            "GITHUB_SERVER_URL",
            "INPUT_OPERATION",
            "INPUT_TAG",
            "INPUT_VERSION",
            "INPUT_DATE",
            "INPUT_CHANGELOGPATH",
        ):
            monkeypatch.delenv(name, raising=False)
        for name, value in environment.items():
            monkeypatch.setenv(name, value)

        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(changelog_content, encoding="utf-8")
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "add", "CHANGELOG.md"], check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial changelog"],
            check=True,
            capture_output=True,
        )
        genesis_hash = subprocess.check_output(
            ["git", "rev-list", "--max-parents=0", "HEAD"], text=True
        ).strip()
        result = subprocess.run(
            ["irnas-changelog-action", "--github-action"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == expected_exit_code
        release_notes = ""
        if output_path.exists():
            release_notes = (
                output_path.read_text(encoding="utf-8")
                .removeprefix("release-notes<<EOF\n")
                .removesuffix("\nEOF\n")
            )
        return (
            changelog.read_text(encoding="utf-8"),
            release_notes,
            genesis_hash,
            result.stderr,
        )

    return run
