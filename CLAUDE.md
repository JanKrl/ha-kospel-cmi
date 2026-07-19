# CLAUDE.md — AI Agent Context for ha-kospel-cmi

This file provides structured context for Claude, Antigravity, and similar AI coding agents working on this repository.

For human-readable documentation, start with [README.md](README.md).

---

## Project Identity

- **Name**: ha-kospel-cmi
- **Type**: Home Assistant custom integration (HACS-compatible) + monorepo for `kospel-cmi-lib`
- **Purpose**: Control and monitor Kospel electric heaters via local network (HTTP API)
- **Supported devices**: EKCO.M3 (device support is defined in the library)
- **License**: Apache 2.0
- **Owner**: @JanKrl
- **Repository**: https://github.com/JanKrl/ha-kospel-cmi

## Monorepo Structure

This repository is a **uv workspace monorepo** containing two packages:

| Package | Path | Distributed via |
|---------|------|-----------------|
| `kospel-cmi-lib` | `lib/` | [PyPI](https://pypi.org/project/kospel-cmi-lib/) |
| `ha-kospel-cmi` (HA integration) | root (`custom_components/kospel/`) | [HACS](https://hacs.xyz/) |

### Package Boundaries

- **`lib/`** (`kospel-cmi-lib`): All heater communication logic — HTTP transport, register decoding/encoding, device models, simulator. Changes here affect the library PyPI package.
- **Root** (`custom_components/kospel/`): HA integration layer only — entities, coordinator, config flow. This is a thin adapter over the library. No heater communication logic belongs here.
- **`tests/`** (root): HA integration tests.
- **`lib/tests/`**: Library unit tests.

### Commit Message Convention (Mandatory)

This repo uses **squash merges** for regular PRs. The **PR title** becomes the commit on `master` — write it as a [Conventional Commit](https://www.conventionalcommits.org/):

```
feat(lib): add EkcoM4 device support       → lib minor release
fix(ha): debounce connectivity sensor      → HA patch release
chore(ci): update uv version              → no release
docs: update README                        → no release
```

release-please reads file paths (not scopes) to assign commits to packages, but scopes (`lib`/`ha`) are strongly recommended for clarity. Individual branch commits do not matter — only the PR title.

> **Exception:** `release-please` PRs MUST be **merge committed** (Create a merge commit). Do not squash-merge release PRs, as this breaks the automated release tracking.

**Breaking changes**: add `BREAKING CHANGE: <description>` as a footer in the PR description body.

## Architecture Overview

This integration is a **thin Home Assistant layer** on top of the external [kospel-cmi-lib](https://pypi.org/project/kospel-cmi-lib/) library.

```
┌─────────────────────────────────────────────────────┐
│  Home Assistant                                      │
│  ┌───────────────────────────────────────────────┐  │
│  │  custom_components/kospel/ (this repo)        │  │
│  │  ┌──────────┐  ┌────────────────────────────┐ │  │
│  │  │config_flow│  │ Entities:                  │ │  │
│  │  │          │  │  climate.py                 │ │  │
│  │  └──────────┘  │  water_heater.py            │ │  │
│  │       │        │  sensor.py                  │ │  │
│  │       ▼        │  binary_sensor.py           │ │  │
│  │  ┌──────────┐  │  number.py                  │ │  │
│  │  │coordinator│──│  select.py                  │ │  │
│  │  └──────────┘  └────────────────────────────┘ │  │
│  └───────────┬───────────────────────────────────┘  │
│              │                                       │
│  ┌───────────▼───────────────────────────────────┐  │
│  │  kospel-cmi-lib (installed via manifest.json)  │  │
│  │  EkcoM3 controller → Backend → Registers       │  │
│  └───────────┬───────────────────────────────────┘  │
│              │                                       │
│  ┌───────────▼──────┐                                │
│  │  Heater HTTP API  │  (local network)              │
│  └──────────────────┘                                │
└─────────────────────────────────────────────────────┘
```

**Key separation**: All heater communication logic (transport, register decoding/encoding, device models) lives in `kospel-cmi-lib`. This repo only contains the Home Assistant integration layer.

## File Map

### Integration Source (`custom_components/kospel/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Integration entry point. Sets up backend (HTTP or YAML), creates `EkcoM3` controller, initializes coordinator. |
| `manifest.json` | HA integration manifest. Declares domain `kospel`, requirements (`aiohttp`, `kospel-cmi-lib`), dependencies (`http`, `network`). |
| `const.py` | Constants, configuration keys, helper functions (`get_device_info`, `get_device_identifier`, `get_refresh_delay_after_set`). |
| `coordinator.py` | `KospelDataUpdateCoordinator` — polls heater via `EkcoM3.refresh()`, tracks communication failures with debounce threshold. |
| `config_flow.py` | Config flow: network scan discovery, manual IP entry, YAML dev mode. Options flow for refresh delay. Includes V1→V2 migration. |
| `climate.py` | Main climate entity. HVAC modes: off/heat/auto. Presets: winter/summer/party/vacation. Target temp writable only in heat (manual) mode. |
| `water_heater.py` | DHW/CWU entity. **Read-only for writes** — displays current/target water temperature and operation mode, but write actions are intentionally no-ops. |
| `sensor.py` | Temperature sensors (CH, DHW, outside, setpoints), pressure, power (kW→W conversion), valve position, heating mode, max power limit. Contains deprecated `KospelHeatingStatusSensor` (to be removed in v1.0.0). |
| `binary_sensor.py` | Connectivity binary sensor (debounced communication status). |
| `number.py` | Room preset temperatures (economy/comfort/comfort+/comfort−), DHW preset temperatures (eco/comfort), outside temperature switch-off threshold. EntityCategory.CONFIG. |
| `select.py` | Boiler max power step selector (2/4/6/8 kW for EKCO.M3). EntityCategory.CONFIG. |
| `strings.json` | English UI strings and entity names. |
| `translations/pl.json` | Polish translations. |
| `brand/` | Brand images (icon.png, logo.png, dark variants) for HA 2026.3+. |
| `data/state.yaml` | YAML backend state file (development/testing only). |

### Tests (`tests/`)

| File | Purpose |
|------|---------|
| `conftest.py` | Shared fixtures: mock sessions, sample registers, EkcoM3 controller instances. |
| `test_climate_entity.py` | Climate entity unit tests (HVAC modes, presets, temperature writes). |
| `test_config_flow.py` | Config flow tests (all steps, validation, migration, options). |
| `test_sensor_entity.py` | Sensor entity tests (temperatures, pressure, power, heating status). |
| `test_number_entity.py` | Number entity tests (preset temperature read/write). |
| `test_select_entity.py` | Select entity tests (boiler max power). |
| `test_water_heater_entity.py` | Water heater entity tests. |
| `test_kospel_library_contract.py` | Verifies expected imports from kospel-cmi-lib work. |
| `integration/test_api_communication.py` | HTTP backend integration tests. |
| `integration/test_mock_mode.py` | YAML backend integration tests. |
| `integration/test_water_heater_registers.py` | Water heater register-level tests. |

### Project Config

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependency groups (dev), pytest/coverage config. |
| `hacs.json` | HACS metadata (name, HA minimum version, persistent directory). |
| `.python-version` | Python version pin. |
| `uv.lock` | Dependency lockfile (managed by `uv`). |

## Key Conventions

### Import Rules

```python
# External library: absolute imports from kospel-cmi-lib
from kospel_cmi.controller.device import EkcoM3
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend
from kospel_cmi.registers.enums import HeaterMode, HeatingStatus

# Within integration: relative imports
from .const import DOMAIN
from .coordinator import KospelDataUpdateCoordinator
```

### Naming Convention

- **Code identifiers** (entity translation keys, variable names, comments, tests): **English** terminology
  - Use `CH` (central heating) not `CO` in code
  - Use `DHW` (domestic hot water) not `CWU` in code
- **Library compatibility fields**: Keep library naming where required
  - `co_heating_status`, `cwu_heating_status`, `cwu_mode` — these are `kospel-cmi-lib` property names
  - Map them to English translation keys in integration code
- **User-facing labels**: Localized in `strings.json` (English) and `translations/pl.json` (Polish)

### Entity Patterns

All entities follow this pattern:
1. Extend `CoordinatorEntity[KospelDataUpdateCoordinator]` + the relevant HA entity class
2. Set `_attr_has_entity_name = True`
3. Use `_attr_translation_key` for naming (not hardcoded `_attr_name`)
4. Get device info via `get_device_info(entry)` from `const.py`
5. Build unique_id via `get_device_identifier(entry)` + suffix
6. Check availability via `self.coordinator.communication_ok` (debounced)
7. Read state from `self.coordinator.data` (returns `EkcoM3` instance)
8. For write operations: call async setter on controller → `async_write_ha_state()` → sleep `get_refresh_delay_after_set()` → `coordinator.async_request_refresh()`

### Write Operation Pattern

Every write operation follows this exact sequence:

```python
async def async_set_something(self, value) -> None:
    controller: EkcoM3 = self.coordinator.data
    try:
        await controller.set_something(value)
    except KospelError as err:
        _LOGGER.error("Failed to set something: %s", err)
        raise HomeAssistantError(f"Failed to set something: {err}") from err
    self.async_write_ha_state()
    await asyncio.sleep(get_refresh_delay_after_set(self.coordinator.entry))
    await self.coordinator.async_request_refresh()
```

## Entity Model — Constraints and Gotchas

### Climate Entity
- **Target temperature is writable only in `heat` (manual) HVAC mode**. Attempting to set temperature in `off` or `auto` raises `HomeAssistantError`.
- `auto` mode defaults to `HeaterMode.WINTER` when set without a preset.
- `async_turn_on()` activates AUTO mode (winter program).

### Water Heater Entity
- **Intentionally read-only for writes**. `async_set_temperature()` and `async_set_operation_mode()` are no-ops that log debug messages.
- DHW behavior is driven by the heater device and the climate entity's HVAC/preset modes.
- `target_temperature` reads the live CWU supply setpoint from register `0b2f` (firmware output), not the static preset registers.

### Sensor Entities
- Power sensor converts from kW (library) to W (HA) by multiplying × 1000.
- Max power limit sensor also converts kW→W and uses `EntityCategory.DIAGNOSTIC`.
- `KospelHeatingStatusSensor` (ch_heating, dhw_heating) is **deprecated** — will be removed in v1.0.0. Use `KospelHeatingModeSensor` instead.
- `KospelHeatingModeSensor` combines CH and DHW status into a single state (off/idle/ch/dwh) since they never run simultaneously.

### Number Entities
- Room presets: 10.0–25.0°C, step 0.1
- DHW presets: 30.0–80.0°C, step 0.1
- Outside temperature threshold: 0–30°C, step 0.1

### Select Entity
- Boiler max power options are device-specific. EKCO.M3 uses 2/4/6/8 kW steps.
- Options are mapped via `BoilerMaxPowerIndex` enum from the library.

## Config Flow

### Setup Paths
1. **Network scan** (`network_scan`): Scans all IPv4 subnets from enabled adapters. Max 1024 hosts per subnet.
2. **Manual entry** (`manual`): User provides heater IP + device ID (default 65).
3. **YAML** (`yaml`): Development mode, no heater needed. State stored in `custom_components/kospel/data/state.yaml`.

### Disabled: DHCP Auto-Discovery
MAC-based auto-discovery via DHCP is **implemented but intentionally hidden** from the UI. The expected Kospel OUI prefix (`70b3d5249`) did not match on a real device. Code is preserved for future re-enabling once OUI matching is verified.

### Config Entry Migration
V1→V2 migration converts `simulation_mode` boolean to `backend_type` string (`"http"` or `"yaml"`).

### Options Flow
Single option: `refresh_delay_after_set` (0.5–5.0 seconds, default 1.0).

## Backend Types

| Type | Class | Use Case |
|------|-------|----------|
| HTTP | `HttpRegisterBackend` | Real heater. Requires heater IP + device ID. API URL: `http://{ip}/api/dev/{id}` |
| YAML | `YamlRegisterBackend` | Development. State file at `custom_components/kospel/data/state.yaml` |

## Communication & Availability

- Coordinator polls every **15 seconds** (`SCAN_INTERVAL`).
- Entities report **unavailable** after `COMMUNICATION_FAILURE_THRESHOLD` consecutive failures (~90 seconds at default scan interval).
- `strict_refresh=True` on `EkcoM3`: incomplete register batches raise `IncompleteRegisterRefreshError` without mutating the cache.
- Errors are caught and re-raised as `UpdateFailed` with appropriate logging.

## Development Commands

```bash
# Install all dependencies for both packages (including dev groups)
uv sync --all-groups

# Run HA integration tests
uv run python -m pytest tests/ -v

# Run HA integration tests with coverage
uv run python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Run library (kospel-cmi-lib) tests
# (from repo root)
uv run python -m pytest lib/tests/ -v
# or equivalently, from lib/ directory:
uv run python -m pytest tests/ -v  # (working-directory: lib)

# Lint all packages from workspace root
uv run ruff check .
```

## Release Process

Releases are driven by [release-please](https://github.com/googleapis/release-please) via `.github/workflows/release-please.yaml`.

- **Library** (`lib-v*` tags): Fully automated. Merge the release-please Release PR using a **merge commit** → git tag created → PyPI publish triggered automatically via OIDC.
- **HA integration** (`v*` tags): Semi-automated. Merge the release-please Release PR using a **merge commit** → Draft GitHub Release created → you enrich release notes and click Publish → HACS notifies users.

For the full release workflow and commit conventions, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Common Pitfalls

1. **Don't import from `kospel_cmi` using relative paths** — it's an installed package, use absolute imports.
2. **Don't make the water heater entity writable** — the read-only design is intentional. DHW is controlled via device firmware and climate entity.
3. **Don't forget the refresh delay** after write operations — the heater needs time to persist register changes.
4. **Don't remove DHCP discovery code** — it's intentionally kept for future use even though it's hidden from the UI.
5. **Don't use `_attr_name` for entity naming** — use `_attr_translation_key` and `strings.json` for all user-facing names.
6. **Don't use `CO`/`CWU` in new code identifiers** — use `CH`/`DHW` in English. Library property names like `co_heating_status` are exceptions (they match the library API).
7. **Power values**: The library reports kW but HA expects W. Always multiply by 1000 when creating power sensors.
8. **Config flow VERSION is 2** — any structural changes to config entry data require a new migration step.

## AI Agent Behavioral Guidelines

1. **Commit and Push Approval**: NEVER push commits to an upstream remote branch (e.g. `origin`) without explicit prior approval from the user.
2. **Force Pushing**: NEVER use force pushes (`--force` or `-f`) without explicit prior approval from the user. When asking for approval, you MUST provide a clear and detailed explanation of exactly why a force push is necessary (e.g., rewriting history, fixing a broken rebase) and what it will overwrite.

## References

- [README.md](README.md) — User-facing documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) — Developer guide: setup, commit conventions, release process
- [docs/architecture.md](docs/architecture.md) — Architecture diagram
- [docs/technical.md](docs/technical.md) — Technical specification
- [docs/advanced-usage.md](docs/advanced-usage.md) — Advanced usage notes
- [lib/README.md](lib/README.md) — Library (kospel-cmi-lib) documentation
- [Home Assistant Developer Docs](https://developers.home-assistant.io/docs/development_index/) — HA integration development reference
- [kospel-cmi-lib on PyPI](https://pypi.org/project/kospel-cmi-lib/) — Library PyPI page
