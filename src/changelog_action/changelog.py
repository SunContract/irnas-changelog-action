"""Transform changelogs that follow the Keep a Changelog convention."""

from __future__ import annotations

import re

UNRELEASED_HEADING = re.compile(
    r"^## \[Unreleased\][ \t]*$", re.IGNORECASE | re.MULTILINE
)
SECTION_HEADING = re.compile(r"^## \[.*\].*$", re.MULTILINE)
DEFINITION = re.compile(r"^\[([^]]+)\]:\s*(\S+)\s*$", re.MULTILINE)


class ChangelogError(ValueError):
    """Raised when the changelog does not have the required structure."""


def update_changelog(
    content: str,
    *,
    tag: str,
    version: str,
    release_date: str,
    genesis_hash: str,
    repository: str,
    server_url: str,
) -> str:
    """Promote Unreleased to a versioned release and update comparison links."""
    heading = UNRELEASED_HEADING.search(content)
    if heading is None:
        message = "Invalid changelog format: could not find an Unreleased section"
        raise ChangelogError(message)

    section_end = _section_end(content, heading.end())
    if not content[heading.end() : section_end].strip():
        message = "Invalid changelog format: Unreleased section must not be empty"
        raise ChangelogError(message)

    previous_tag = _previous_tag(content)
    released_heading = f"## [Unreleased]\n\n## [{version}] - {release_date}"
    updated = content[: heading.start()] + released_heading + content[heading.end() :]
    return _replace_definitions(
        updated,
        tag=tag,
        version=version,
        previous_tag=previous_tag,
        genesis_hash=genesis_hash,
        repository=repository,
        server_url=server_url,
    )


def release_notes(content: str, version: str) -> str:
    """Return the body of a released version section without its heading."""
    heading = re.compile(
        rf"^## \[{re.escape(version)}\](?:[ \t]*-[^\n]*)?$", re.MULTILINE
    ).search(content)
    if heading is None:
        message = f"Could not find release section for version {version}"
        raise ChangelogError(message)

    end = SECTION_HEADING.search(content, heading.end())
    definitions = DEFINITION.search(content, heading.end())
    candidates = [match.start() for match in (end, definitions) if match is not None]
    body_end = min(candidates) if candidates else len(content)
    return content[heading.end() : body_end].lstrip("\n")


def _section_end(content: str, start: int) -> int:
    next_heading = SECTION_HEADING.search(content, start)
    next_definition = DEFINITION.search(content, start)
    candidates = [
        match.start() for match in (next_heading, next_definition) if match is not None
    ]
    return min(candidates) if candidates else len(content)


def _previous_tag(content: str) -> str | None:
    definitions = list(DEFINITION.finditer(content))
    unreleased_index = next(
        (
            index
            for index, definition in enumerate(definitions)
            if definition.group(1).lower() == "unreleased"
        ),
        None,
    )
    if unreleased_index is None or unreleased_index + 1 >= len(definitions):
        return None

    url = definitions[unreleased_index + 1].group(2)
    if "..." not in url:
        message = "Invalid changelog format: compare URL is not standard"
        raise ChangelogError(message)
    return url.rsplit("...", maxsplit=1)[1]


def _replace_definitions(
    content: str,
    *,
    tag: str,
    version: str,
    previous_tag: str | None,
    genesis_hash: str,
    repository: str,
    server_url: str,
) -> str:
    definitions = list(DEFINITION.finditer(content))
    unreleased = next(
        (
            definition
            for definition in definitions
            if definition.group(1).lower() == "unreleased"
        ),
        None,
    )
    release_compare = previous_tag or genesis_hash
    new_definitions = (
        f"[Unreleased]: {server_url}/{repository}/compare/{tag}...HEAD\n\n"
        f"[{version}]: {server_url}/{repository}/compare/{release_compare}...{tag}"
    )
    if unreleased is None:
        separator = "" if content.endswith("\n\n") else "\n"
        return f"{content}{separator}{new_definitions}\n"
    return (
        f"{content[: unreleased.start()]}{new_definitions}{content[unreleased.end() :]}"
    )
