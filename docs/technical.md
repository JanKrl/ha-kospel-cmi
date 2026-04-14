# Technical Specifications

Technical documentation for the Kospel Heater Home Assistant integration.

## Overview

This project provides a Home Assistant integration for Kospel electric heaters. Heater communication (Transport, Data, Service layers) is provided by the external [kospel-cmi-lib](https://pypi.org/project/kospel-cmi-lib/) package. This repository contains only the Home Assistant integration layer.

**Key Characteristics:**
- Uses `kospel-cmi-lib` for heater API communication
- Config flow choice: HTTP (real device) or YAML (file-based, for development)
- Entities: climate, number (room preset temperatures, **Configuration**), select (boiler max power, **Configuration**), sensors (including max power limit diagnostic), water heater
- `uv` for dependency management, `pytest` for testing

## Home Assistant Integration

### Naming Convention

- Internal code identifiers (entity translation keys, variable names, comments, tests) use English terminology.
- Device-library compatibility fields keep library naming where required (for example `co_heating_status`, `cwu_heating_status`) and are mapped to English integration keys.
- User-facing labels are localized in translation files:
  - `strings.json`: English labels (`CH`, `DHW`)
  - `translations/pl.json`: Polish labels (`CO`, `CWU`)

### Import Rules

The integration uses **kospel-cmi-lib** for heater communication. Imports use absolute paths to the installed package:

```python
# Correct: Absolute imports from kospel-cmi-lib (installed via manifest requirements)
from kospel_cmi.controller.device import EkcoM3
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend
from kospel_cmi.registers.enums import HeaterMode

# Device controller: backend only; strict_refresh ensures full register batch (see library)
controller = EkcoM3(backend=..., strict_refresh=True)

# Within integration: use relative imports
from .const import DOMAIN
from .coordinator import KospelDataUpdateCoordinator
```

kospel-cmi-lib is installed by Home Assistant when loading the integration (via `manifest.json` requirements). Integration modules within `custom_components/kospel/` use relative imports (`.`) for each other.

### Integration Structure

```
custom_components/kospel/
├── __init__.py          # Integration entry point
├── manifest.json        # requirements: aiohttp, kospel-cmi-lib
├── brand/               # Local brand images (Home Assistant 2026.3+)
│   ├── icon.png         # Square icon (light UI)
│   ├── logo.png         # Logo (light UI)
│   ├── dark_icon.png    # Square icon (dark UI)
│   └── dark_logo.png    # Logo (dark UI)
├── config_flow.py      # Configuration UI (HTTP or YAML backend choice)
├── coordinator.py      # Data update coordinator
├── climate.py          # Climate entity
├── number.py           # Number entities (room preset temperatures)
├── select.py           # Select entities (boiler max power step)
├── sensor.py           # Sensor entities
├── water_heater.py     # Water heater entity
├── const.py            # Constants
└── strings.json        # UI strings
```

### Backend Types

- **HTTP**: Connects to a real heater. Requires heater IP and device ID.
- **YAML**: File-based backend for development. State stored at `custom_components/kospel/data/state.yaml`.

## Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
└── integration/             # Integration tests
    ├── test_api_communication.py
    └── test_mock_mode.py
```

Library layer tests live in the kospel-cmi-lib repository.

### Running Tests

```bash
uv sync --all-groups
uv run python -m pytest tests/ -v
```

## Dependencies

- **Runtime**: aiohttp, kospel-cmi-lib (pinned in manifest.json)
- **Development**: pytest, pytest-asyncio, pytest-cov, pytest-mock, aioresponses, pyyaml
- **Package manager**: `uv`

## References

- **Architecture**: `docs/architecture.md`
- **Status**: `docs/status.md`
- **Installation**: `INSTALLATION.md`
