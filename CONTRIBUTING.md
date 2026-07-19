# Contributing to ha-kospel-cmi

Thanks for your interest in contributing!

This repository is a **monorepo** containing two packages:

| Package | Path | Distributed via |
|---------|------|-----------------|
| `kospel-cmi-lib` | `lib/` | [PyPI](https://pypi.org/project/kospel-cmi-lib/) |
| `ha-kospel-cmi` (HA integration) | root (`custom_components/kospel/`) | [HACS](https://hacs.xyz/) |

---

## Development Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management as a **workspace** — both packages share a single lock file at the repo root.

```bash
# Clone the repository
git clone https://github.com/JanKrl/ha-kospel-cmi.git
cd ha-kospel-cmi

# Install all dependencies for both packages (including dev groups)
uv sync --all-groups
```

---

## Running Tests

```bash
# HA integration tests
uv run python -m pytest tests/ -v

# HA integration tests with coverage
uv run python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Library (kospel-cmi-lib) tests
uv run python -m pytest tests/ -v
# (run from lib/ directory, or use working-directory: lib in scripts)

# Lint both packages (Ruff covers entire workspace from root)
uv run ruff check .
```

---

## Testing Unreleased Library Changes in Home Assistant

If you make changes to `lib/` (the library) and want to test them in a real Home Assistant instance **before** they are published to PyPI, do not merge to `master` yet. Instead, update your Home Assistant instance to pull the library directly from your development branch.

1. Open `custom_components/kospel/manifest.json` on your Home Assistant instance.
2. Locate the `requirements` array.
3. Change the `kospel-cmi-lib` entry to point to your branch using pip's git support. For example:

```json
  "requirements": [
    "aiohttp>=3.13.3",
    "kospel-cmi-lib @ git+https://github.com/JanKrl/ha-kospel-cmi.git@your-branch-name#subdirectory=lib"
  ],
```

4. Restart Home Assistant. It will download the exact code from your branch.
5. **Important:** Remember to revert this change in your `manifest.json` after testing, or let HACS overwrite it when the official release is ready.

---

## Code Style

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) — `uv run ruff check .`
- **Type hints**: Required for all public methods (Home Assistant convention)
- **Docstrings**: Required for all public classes and methods
- **Style**: PEP 8

---

## Commit Messages — Conventional Commits (Required)

This project uses [Conventional Commits](https://www.conventionalcommits.org/) to drive automated versioning via [release-please](https://github.com/googleapis/release-please).

> [!IMPORTANT]
> **The repository uses squash merges for regular PRs.** This means the **PR title** is the commit message that ends up on `master`. Individual commits on your feature branch don't matter — write the PR title carefully.
>
> **Exception:** `release-please` PRs MUST be **merge committed** (Create a merge commit). Do not squash-merge release PRs, as this breaks the automated release tracking.

### Format

```
<type>(<optional-scope>): <short description>
```

### Types and Their Effect on Versioning

| Type | Version bump | When to use |
|------|-------------|-------------|
| `fix` | patch | Bug fix |
| `feat` | minor | New feature (backward-compatible) |
| `BREAKING CHANGE` (in PR body) | major | Removes or changes existing behavior |
| `chore` | none | Maintenance, tooling, dependencies |
| `docs` | none | Documentation only |
| `refactor` | none | Code restructure, no behavior change |
| `test` | none | Adding or fixing tests |
| `ci` | none | CI/CD changes |
| `perf` | none | Performance improvement |
| `style` | none | Formatting, whitespace |

> [!IMPORTANT]
> **Breaking changes**: Add `BREAKING CHANGE: <description>` as a footer line in the **PR description body** (not in the title). GitHub includes the PR body in the squash commit message, so release-please will detect it.
>
> Example PR description:
> ```
> This PR redesigns the HeaterController connection API.
>
> BREAKING CHANGE: HeaterController.connect() is now an async context manager.
> The old .start()/.stop() API is removed.
> ```

### Scopes (Recommended)

Using a scope in the PR title makes it immediately clear which package is affected:

| Scope | Meaning |
|-------|---------|
| `lib` | Change in `lib/` — affects `kospel-cmi-lib` |
| `ha` | Change in HA integration — affects `custom_components/kospel/` |
| *(none)* | Root-level change (CI, docs, monorepo config) — no release |

Scopes are **optional** for the automation (release-please uses file paths to detect which package a commit affects), but strongly recommended for human readability.

### PR Title Examples

```bash
# Library — patch release
fix(lib): correct temperature register decoding for EKCO.M3

# Library — minor release
feat(lib): add support for EkcoM4 device type

# Library — major release (BREAKING CHANGE in PR body)
feat(lib): redesign HeaterController async interface

# HA integration — minor release
feat(ha): expose outside temperature threshold as number entity

# HA integration — patch release
fix(ha): debounce connectivity binary sensor to avoid false offline events

# No release triggered (chore/docs/refactor/test/ci)
chore(ci): pin uv to v0.5.x in all workflows
docs: add monorepo structure to README
test(lib): add register decoding edge case coverage
refactor(ha): extract shared entity base class
```

---

## Branch Naming (Recommended, Not Enforced)

```
feat/lib/<short-description>    # e.g. feat/lib/ekco-m4-support
fix/lib/<short-description>     # e.g. fix/lib/temperature-decoding
feat/ha/<short-description>     # e.g. feat/ha/outside-temp-entity
fix/ha/<short-description>      # e.g. fix/ha/binary-sensor-debounce
chore/<short-description>       # e.g. chore/update-ci-uv-version
```

---

## Pull Request Guidelines

1. Branch off from `master`.
2. Use the branch naming convention above.
3. Write or update tests for your changes.
4. Ensure all tests and lint pass locally before submitting.
5. Keep PRs focused — one feature or fix per PR.
6. **Write the PR title as a conventional commit message** — this becomes the commit on `master`.
7. **Link related issues using `Relates to #<issue>`**. Do *not* use `Fixes #<issue>` or `Closes #<issue>`, as we want issues to remain open until the actual release is published. Our automated workflows will correctly assign the `Closes #<issue>` keyword to the `release-please` PR.
8. Update documentation if your change affects user-facing behavior or developer patterns.

---

## Release Process

### How It Works

Releases are managed automatically by [release-please](https://github.com/googleapis/release-please):

1. You merge PRs to `master` with conventional commit titles.
2. release-please opens/updates a **Release PR** per package, accumulating unreleased changes.
3. You merge the Release PR using a **merge commit** when you're ready to ship.
4. A git tag and GitHub Release are created automatically.
   - **Library** (`lib-v1.1.0` tag): PyPI publish runs automatically (OIDC, no token needed).
   - **HA integration** (`v0.2.0` tag): A **Draft** GitHub Release is created. You enrich the release notes and click Publish — HACS then notifies users.

### Batching Multiple PRs into One Release

You don't have to merge the Release PR after every single PR. Let it accumulate:

- Merge 5 PRs → Release PR shows all 5 changes with a single version bump
- When you're happy with the batch, merge the Release PR
- Everything ships in one version

### Library Release (Automatic)

No manual steps needed — release-please and PyPI publishing handle everything once you merge the Release PR.

### HA Integration Release (Semi-Manual)

After merging the HA Release PR:
1. Go to the **Draft GitHub Release** that was created automatically.
2. Edit the release notes to be user-friendly: describe what changed per entity, highlight breaking changes, list any migration steps.
3. Click **Publish release** — HACS immediately detects the new version.

> [!NOTE]
> HACS only sees **published** releases. The draft is invisible to users until you publish it, giving you full control over timing.

---

## Adding a New HA Entity

1. Create a new entity module in `custom_components/kospel/` (e.g., `switch.py`).
2. Follow the entity pattern documented in [CLAUDE.md](CLAUDE.md#entity-patterns).
3. Register the platform in `PLATFORMS` list in `__init__.py`.
4. Add translation keys in `strings.json` and `translations/pl.json`.
5. Write tests covering the entity's read properties and write operations.

## Adding Support for a New Kospel Device

All device communication logic lives in the **library** (`lib/`), not the HA integration. To add a new device:

1. Add device support in `lib/src/kospel_cmi/` (new controller class, registers, device model).
2. Add library tests in `lib/tests/`.
3. Update the HA integration to expose new device-specific entities if needed.
4. Use a `feat(lib): add support for <device>` PR title for a proper minor version bump.

---

## Reporting Issues

Use the [GitHub issue templates](https://github.com/JanKrl/ha-kospel-cmi/issues/new/choose) for bug reports and feature requests.

When reporting bugs, include:
- Home Assistant logs from `custom_components.kospel`
- Whether the bug is in the HA integration layer or the communication library
- Device model and firmware version if relevant
