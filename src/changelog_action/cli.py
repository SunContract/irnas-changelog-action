"""Command-line and GitHub Action entry point."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from .changelog import ChangelogError, release_notes, update_changelog


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create or extract a Keep a Changelog release."
    )
    parser.add_argument(
        "operation",
        nargs="?",
        choices=("release", "extract"),
        default=None,
        help="Operation to perform; defaults to release.",
    )
    parser.add_argument("--tag", help="Release tag, such as v1.2.3")
    parser.add_argument(
        "--version", help="Release version; deprecated in favor of --tag"
    )
    parser.add_argument(
        "--date", dest="release_date", help="Release date in YYYY-MM-DD format"
    )
    parser.add_argument("--changelog-path", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--repository", help="GitHub repository in owner/repo format")
    parser.add_argument("--github-action", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Update a changelog and emit release notes when running as an Action."""
    args = parse_args(argv)
    try:
        operation = args.operation or os.environ.get("INPUT_OPERATION", "release")
        tag, version = _tag_and_version(args)
        path = _changelog_path(args)
        content = path.read_text(encoding="utf-8")
        if operation == "extract":
            notes = release_notes(content, version)
        else:
            repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
            if (
                not repository
                or len(repository.split("/")) != 2
                or any(not component for component in repository.split("/"))
            ):
                raise ChangelogError("A repository in owner/repo format is required")
            server_url = os.environ.get(
                "GITHUB_SERVER_URL", "https://github.com"
            ).rstrip("/")
            release_date = (
                args.release_date
                or os.environ.get("INPUT_DATE")
                or date.today().isoformat()
            )
            updated = update_changelog(
                content,
                tag=tag,
                version=version,
                release_date=release_date,
                genesis_hash=_genesis_hash(),
                repository=repository,
                server_url=server_url,
            )
            path.write_text(updated, encoding="utf-8")
            notes = ""
        if args.github_action:
            _set_github_output("release-notes", notes)
        else:
            print(notes)
    except (ChangelogError, OSError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


def _tag_and_version(args: argparse.Namespace) -> tuple[str, str]:
    tag = args.tag or os.environ.get("INPUT_TAG")
    version = args.version or os.environ.get("INPUT_VERSION")
    if tag:
        return tag, tag.removeprefix("v")
    if version:
        return version, version
    raise ChangelogError("Neither tag nor version specified")


def _changelog_path(args: argparse.Namespace) -> Path:
    if args.github_action and "INPUT_CHANGELOGPATH" in os.environ:
        return Path(os.environ["INPUT_CHANGELOGPATH"])
    return args.changelog_path


def _genesis_hash() -> str:
    return subprocess.check_output(
        ["git", "rev-list", "--max-parents=0", "HEAD"], text=True
    ).splitlines()[0]


def _set_github_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path is None:
        return
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"{name}<<EOF\n{value}\nEOF\n")


if __name__ == "__main__":
    raise SystemExit(main())
