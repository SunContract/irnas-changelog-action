"""Tests for invoking the program as a GitHub Action."""

from conftest import RunChangelogAction

STANDARD_CHANGELOG = """# Changelog

## [Unreleased]

### Added

- New feature.

## [1.0.0] - 2024-01-01

### Added

- Initial release.

[Unreleased]: https://github.com/acme/widget/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/acme/widget/compare/abc123...v1.0.0
"""

STANDARD_RELEASED_CHANGELOG = """# Changelog

## [Unreleased]

## [1.1.0] - 2024-02-03

### Added

- New feature.

## [1.0.0] - 2024-01-01

### Added

- Initial release.

[Unreleased]: https://github.com/acme/widget/compare/v1.1.0...HEAD

[1.1.0]: https://github.com/acme/widget/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/acme/widget/compare/abc123...v1.0.0
"""

FIRST_RELEASE_CHANGELOG = """# Changelog

## [Unreleased]

- First release.
"""

FIRST_RELEASED_CHANGELOG = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-01

- First release.

[Unreleased]: https://github.com/acme/widget/compare/v1.0.0...HEAD

[1.0.0]: https://github.com/acme/widget/compare/{genesis_hash}...v1.0.0
"""

RELEASED_CHANGELOG = """# Changelog

## [1.0.0] - 2024-01-01

### Added

- Initial release.
"""

EXTRACTED_RELEASED_CHANGELOG = """### Added

- Initial release.
"""

EMPTY_UNRELEASED_CHANGELOG = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-01

- Initial release.
"""

MISSING_VERSION_CHANGELOG = """# Changelog

## [1.0.0] - 2024-01-01

- Initial release.
"""

ENTERPRISE_CHANGELOG = """# Changelog

## [Unreleased]

- Enterprise release.
"""

ENTERPRISE_RELEASED_CHANGELOG = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-01

- Enterprise release.

[Unreleased]: https://github.example.com/engineering/widget/compare/v1.0.0...HEAD

[1.0.0]: https://github.example.com/engineering/widget/compare/{genesis_hash}...v1.0.0
"""


def test_release_promotes_unreleased_and_leaves_release_notes_empty(
    run_changelog_action: RunChangelogAction,
) -> None:
    """The release operation modifies the changelog and leaves release-notes empty."""
    updated, release_notes, _, _ = run_changelog_action(
        STANDARD_CHANGELOG,
        INPUT_TAG="v1.1.0",
        INPUT_DATE="2024-02-03",
    )
    assert release_notes == ""
    assert updated == STANDARD_RELEASED_CHANGELOG


def test_first_release_leaves_release_notes_empty(
    run_changelog_action: RunChangelogAction,
) -> None:
    """The first release uses the Git genesis commit and leaves release-notes empty."""
    updated, release_notes, genesis_hash, _ = run_changelog_action(
        FIRST_RELEASE_CHANGELOG,
        INPUT_TAG="v1.0.0",
        INPUT_DATE="2024-01-01",
    )
    assert release_notes == ""
    assert updated == FIRST_RELEASED_CHANGELOG.format(genesis_hash=genesis_hash)


def test_extract_sets_release_notes_without_modifying_changelog(
    run_changelog_action: RunChangelogAction,
) -> None:
    """The extract operation sets release-notes without altering the changelog."""
    updated, release_notes, _, _ = run_changelog_action(
        RELEASED_CHANGELOG,
        INPUT_OPERATION="extract",
        INPUT_VERSION="1.0.0",
    )
    assert release_notes == EXTRACTED_RELEASED_CHANGELOG
    assert updated == RELEASED_CHANGELOG


def test_release_rejects_an_empty_unreleased_section(
    run_changelog_action: RunChangelogAction,
) -> None:
    """The release operation rejects an Unreleased section without content."""
    _, _, _, error = run_changelog_action(
        EMPTY_UNRELEASED_CHANGELOG,
        expected_exit_code=1,
        INPUT_TAG="v1.1.0",
    )
    assert "Unreleased section must not be empty" in error


def test_extract_rejects_a_missing_version(
    run_changelog_action: RunChangelogAction,
) -> None:
    """The extract operation reports an error when the requested version is absent."""
    _, _, _, error = run_changelog_action(
        MISSING_VERSION_CHANGELOG,
        expected_exit_code=1,
        INPUT_OPERATION="extract",
        INPUT_VERSION="2.0.0",
    )
    assert "Could not find release section for version 2.0.0" in error


def test_release_uses_server_url_and_organization(
    run_changelog_action: RunChangelogAction,
) -> None:
    """Comparison links use the configured GitHub server and organization repository path."""
    updated, release_notes, genesis_hash, _ = run_changelog_action(
        ENTERPRISE_CHANGELOG,
        INPUT_TAG="v1.0.0",
        INPUT_DATE="2024-01-01",
        GITHUB_SERVER_URL="https://github.example.com/",
        GITHUB_REPOSITORY="engineering/widget",
    )
    assert release_notes == ""
    assert updated == ENTERPRISE_RELEASED_CHANGELOG.format(genesis_hash=genesis_hash)
