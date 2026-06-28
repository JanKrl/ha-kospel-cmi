# Contributing to ha-kospel-cmi

Thanks for your interest in contributing!

## Development Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/JanKrl/ha-kospel-cmi.git
cd ha-kospel-cmi

# Install all dependencies (including dev group)
uv sync --all-groups
```

## Running Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run with coverage
uv run python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

## Code Style

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) — run `uv run ruff check .`
- **Type hints**: Required for all public methods (Home Assistant convention)
- **Docstrings**: Required for all public classes and methods
- **Style**: PEP 8

## Pull Request Guidelines

1. Create a feature branch from `master`.
2. Write or update tests for your changes.
3. Ensure all tests pass before submitting.
4. Keep PRs focused — one feature or fix per PR.
5. Update documentation if your change affects user-facing behavior or developer patterns.

## Architecture Context

See [CLAUDE.md](CLAUDE.md) for a detailed architecture overview, file map, conventions, and common pitfalls. This file is written for AI agents but is equally useful as a human developer reference.

## Adding a New Entity

1. Create a new entity module in `custom_components/kospel/` (e.g., `switch.py`).
2. Follow the entity pattern documented in [CLAUDE.md](CLAUDE.md#entity-patterns).
3. Register the platform in `PLATFORMS` list in `__init__.py`.
4. Add translation keys in `strings.json` and `translations/pl.json`.
5. Write tests covering the entity's read properties and write operations.

## Reporting Issues

Use the [GitHub issue templates](https://github.com/JanKrl/ha-kospel-cmi/issues/new/choose) for bug reports and feature requests. Include Home Assistant logs from `custom_components.kospel` when reporting bugs.
