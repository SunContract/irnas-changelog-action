# IRNAS Changelog Action

Promote the `Unreleased` section of a [Keep a Changelog](https://keepachangelog.com/) file into a
new release. The tool adds a fresh empty `Unreleased` section, updates GitHub comparison links, and
leaves the `release-notes` output empty.

The action can also extract release notes for existing versions without modifying the changelog.

## Command Line

Use [uv](https://docs.astral.sh/uv/) to run it locally:

```shell
uv run irnas-changelog-action \
  --tag v1.2.3 \
  --repository owner/repository
```

The command updates `CHANGELOG.md` in place. The release date defaults to today, and `--version` is
supported for compatibility, though `--tag` is preferred.

Extract release notes without modifying the changelog:

```shell
uv run irnas-changelog-action extract --version 1.2.3
```

## GitHub Action

Use the repository action directly:

```yaml
- uses: IRNAS/irnas-changelog-action@main
  id: changelog
  with:
    tag: v1.2.3
```

The action uses `GITHUB_REPOSITORY` for comparison links and defaults to `CHANGELOG.md` when
`changelogPath` is not set. Its `release-notes` output is empty for this operation. It only modifies
the changelog; it does not commit or push changes.

Extract notes for an existing release without modifying the file:

```yaml
- uses: IRNAS/irnas-changelog-action@main
  id: release_notes
  with:
    operation: extract
    version: 1.2.3

- run: printf '%s\n' '${{ steps.release_notes.outputs.release-notes }}'
```

## Development

```shell
uv sync --all-groups
uv run pytest
uv run ruff check .
```
