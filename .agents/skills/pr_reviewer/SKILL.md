---
name: PR Reviewer
description: Reviews pull requests or branch diffs specifically for the ha-kospel-cmi monorepo. Evaluates standard code quality, Home Assistant patterns, monorepo release-please boundaries, and opportunistic "low-hanging fruits" in touched modules, outputting a single message with 1–5 star severity ratings and clickable code links.
---

# PR Reviewer Skill

When asked to review a Pull Request, branch diff, or staged/unstaged changes in this repository, act as a thorough, pragmatic Senior Engineer & Home Assistant Core Reviewer.

## 1. Review Scope & Checklist

Evaluate the changes against both **general software engineering standards** and **repository-specific rules** (`.agents/AGENTS.md` and `CONTRIBUTING.md`):

### A. Monorepo & Release-Please Compliance
- **Strict Package Separation**: Changes MUST NOT mix `lib/` (`kospel-cmi-lib`) and `custom_components/kospel/` (`ha-kospel-cmi`) in the same PR.
- **Manifest Requirements**: `custom_components/kospel/manifest.json` must only reference versions of `kospel-cmi-lib` that are already published on PyPI (`hassfest` requirement).
- **PR Metadata (if reviewing a GitHub PR)**:
  - Title follows Conventional Commits (`feat(lib): ...`, `fix(ha): ...`, `ci: ...`, `chore: ...`; never `fix(ci)` or `feat(ci)`).
  - Body follows `.github/pull_request_template.md`.
  - Issues are linked with `Relates to #123` (never `Fixes #123` or `Closes #123`).
  - Breaking changes include a `BREAKING CHANGE: <description>` footer in the PR body and touch only one package.

### B. Home Assistant & Kospel Architecture Conventions
- **Boundary Discipline**: All heater communication, register encoding/decoding, and HTTP/YAML transport belong in `lib/`. `custom_components/kospel/` is strictly a thin HA adapter.
- **Imports**: Absolute imports from `kospel_cmi.*`; relative imports within `custom_components/kospel/`.
- **Naming**: English identifiers (`CH` instead of `CO`, `DHW` instead of `CWU`) except where interfacing with legacy library properties (`cwu_mode`). Those exceptions must be communicated to the user and asked to decide whether to rename it or keep the legacy name until the next major release.
- **Entity Conventions**:
  - Extends `CoordinatorEntity[KospelDataUpdateCoordinator]` and the appropriate HA entity base class.
  - Uses `_attr_has_entity_name = True` and `_attr_translation_key` (never hardcoded `_attr_name`).
  - Preserves backward-compatible `unique_id` values (uses `unique_id_suffix` override if renaming settings).
  - Availability delegates to `self.coordinator.communication_ok`.
  - Write operations follow the exact sequence: `await controller.set_*()` (catching `KospelError` → raising `HomeAssistantError`) → `self.async_write_ha_state()` → `await asyncio.sleep(get_refresh_delay_after_set(...))` → `await self.coordinator.async_request_refresh()`.
- **Domain Gotchas**:
  - Power values from `lib/` (kW) multiplied by `1000` for HA (W).
  - Climate target temperature only writable in `heat` (manual) HVAC mode.
  - Config flow `VERSION` bumped with migration if entry data schema changes.
- **Translations & Mocking**:
  - New/changed entities or UI texts updated in both `custom_components/kospel/strings.json` and `custom_components/kospel/translations/pl.json`.

### C. General Code Review Standards
- **Correctness & Edge Cases**: Logic bugs, off-by-one errors, `None`/missing register handling, race conditions, async cancellation safety, resource leaks (unclosed `aiohttp` sessions/timeouts).
- **Security & Robustness**: Input validation in config flow, safe network/HTTP handling, no leaked secrets or unsafe deserialization.
- **Code Style & Typing**: Complete type hints on public methods/classes, docstrings on public APIs, PEP 8 / Ruff compliance, Ponytail simplicity (no over-engineering, dead abstractions, or reinvented stdlib).
- **Testing & Documentation**: Unit/integration tests covering happy paths and error paths; `README.md` (and `lib/README.md` when `lib/` changes) updated for user-facing changes.

### D. "Low-Hanging Fruits" in Touched Modules
In addition to reviewing the diff itself, inspect the **entire files/modules touched by the PR** for quick, high-value opportunistic improvements:
- Unused imports, dead code, or redundant helpers in the same file.
- Missing type hints or outdated docstrings near the modified code.
- Verbose constructs that can be simplified to a stdlib call or one-liner (Ponytail principle).
- Obvious missing edge-case assertions in the corresponding test file.

---

## 2. Severity Rating Scale (1 to 5 Stars)

Rate every finding from **1 to 5 stars**:

- `★★★★★` **(5/5 — Critical / Blocker)**: Breaking bug, data/register corruption, security vulnerability, violation of monorepo package separation, unreleased PyPI version in `manifest.json`, or broken `unique_id` migration. Must be fixed before merge.
- `★★★★☆` **(4/5 — Major)**: Missing error handling (`KospelError` not converted to `HomeAssistantError`), wrong entity write sequence (missing refresh delay), missing translation keys (`strings.json` / `pl.json`), missing tests for new behavior, or significant logic flaw.
- `★★★☆☆` **(3/5 — Moderate)**: Missing `state.yaml` mock data, missing `README.md` update, incomplete type hints on public methods, suboptimal HA entity attributes, or moderate maintainability issues.
- `★★☆☆☆` **(2/5 — Minor)**: Code style/readability improvements, minor refactoring, docstring clarifications, or non-critical test cleanups.
- `★☆☆☆☆` **(1/5 — Nit / Low-Hanging Fruit)**: Trivial polish, naming nits, or opportunistic "low-hanging fruit" cleanups in the surrounding module.

---

## 3. Output Format (Single Consolidated Message)

Deliver the entire review in **one single response message**. Do not split the review across multiple messages or create external artifacts unless explicitly asked.

Order findings from **most severe (`★★★★★`) to least severe (`★☆☆☆☆`)**, and group opportunistic cleanups under a dedicated **Low-Hanging Fruits in Touched Modules** section (also rated 1–5 stars). Every point MUST include clickable markdown links (`file:///absolute/path/to/file#Lstart-Lend`) to the exact code locations.

Use this structure:

```markdown
## 🔍 PR Review Summary
**Scope**: `<lib | ha | mixed (⚠️ violation)>` | **Verdict**: `<Approve | Approve with minor suggestions | Request changes>`

### Findings

1. **`★★★★★` (5/5) — <Short title of the issue>**
   - **Location**: [`filename.py:L42-L55`](file:///home/jan/code/ha-kospel-cmi/path/to/filename.py#L42-L55)
   - **Issue**: <Concise explanation of the problem and why it matters.>
   - **Suggestion**: <Concrete fix or code snippet.>

2. **`★★★☆☆` (3/5) — <Short title of the issue>**
   - **Location**: [`other_file.py:L10-L18`](file:///home/jan/code/ha-kospel-cmi/path/to/other_file.py#L10-L18)
   - **Issue**: <Concise explanation.>
   - **Suggestion**: <Concrete fix.>

### 🍒 Low-Hanging Fruits in Touched Modules

1. **`★★☆☆☆` (2/5) — <Short title of the opportunistic improvement>**
   - **Location**: [`filename.py:L120-L132`](file:///home/jan/code/ha-kospel-cmi/path/to/filename.py#L120-L132)
   - **Opportunity**: <What can be simplified, typed, or cleaned up in the touched module.>
   - **Suggestion**: <Concrete 1-2 line replacement or action.>
```

