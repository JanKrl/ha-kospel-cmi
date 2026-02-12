# Kospel Heater Home Assistant Integration

Home Assistant integration for Kospel electric heaters. Uses the [kospel-cmi-lib](https://pypi.org/project/kospel-cmi-lib/) library for heater communication via their HTTP API.

## Current Status

✅ **Home Assistant Integration Verified**: The integration has been successfully tested and verified to work in Home Assistant. The integration appears correctly in the Home Assistant UI and loads without errors.

During configuration you can choose **HTTP** (real heater device) or **YAML** (file-based, for development). For YAML, state is stored in `custom_components/kospel/data/state.yaml`.

## Architecture

The integration uses the external **kospel-cmi-lib** library for heater communication (Transport, Data, and Service layers) and provides the Home Assistant integration layer:

1. **Layers 1–3 (kospel-cmi-lib)**: Transport (HTTP API, YAML backend), Data (registers, decoders, encoders), Service (HeaterController)
2. **Integration Layer (this repo)**: Home Assistant entities (climate, sensor, switch), config flow, coordinator

Heater communication is provided by **kospel-cmi-lib** (installed via `manifest.json` requirements when loaded in Home Assistant).

### Project Structure

```
home-assistant-kospel/
├── custom_components/     # Home Assistant integration
│   └── kospel/
│       ├── __init__.py    # Integration entry point
│       ├── manifest.json  # Integration metadata
│       ├── config_flow.py # Configuration UI
│       ├── coordinator.py # Data update coordinator
│       ├── climate.py     # Climate entity
│       ├── sensor.py      # Sensor entities
│       ├── switch.py      # Switch entities
│       ├── const.py       # Constants
│       └── strings.json   # UI strings
├── tests/                 # Integration tests
│   ├── conftest.py
│   └── integration/
├── docs/                  # Documentation
│   ├── architecture.md
│   ├── technical.md
│   └── status.md
└── INSTALLATION.md        # Home Assistant installation instructions
```

## Installation (HACS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JanKrl&repository=ha-kospel-cmi&category=integration)

If your Home Assistant instance is [linked to My Home Assistant](https://my.home-assistant.io/), click the badge above to open this repository in HACS and install from there. Otherwise add the repo manually:

1. In HACS go to **Integrations** → **⋮** → **Custom repositories**.
2. Add repository URL: `https://github.com/JanKrl/ha-kospel-cmi`
3. Select category **Integration** and click **Add**.
4. Search for **Kospel Electric Heaters**, install, then restart Home Assistant.
5. Add the integration via **Settings** → **Devices & services** → **Add integration** → **Kospel Electric Heaters**.

See [INSTALLATION.md](INSTALLATION.md) for manual installation and configuration details.

## Testing

```bash
uv sync --all-groups
uv run python -m pytest tests/ -v
```

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full text.
