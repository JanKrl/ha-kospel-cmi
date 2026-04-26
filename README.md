# Kospel Electric Heaters for Home Assistant

<p align="center">
  <img src="custom_components/kospel/brand/icon.png" alt="Kospel K-CMI" width="160" height="160">
</p>

Control and monitor compatible Kospel electric heaters from Home Assistant using local network communication.

> [!WARNING]
> This is an unofficial, community-maintained integration and is not affiliated with or endorsed by Kospel.
> Use it at your own responsibility.

## Capabilities

This integration allows you to:

- **Control central heating from a single climate entity**:
  - Set HVAC mode: `off`, `heat`, `auto`.
  - Use presets in auto mode: `winter`, `summer`, `party`, `vacation`.
  - Adjust target temperature in manual heat mode.
- **Monitor key operating values**:
  - CH and DHW temperatures.
  - CH and DHW target temperatures.
  - Instant power and pressure.
  - CH/DHW heating status and valve position.
- **Manage selected configuration values**:
  - Room preset temperatures (`eco`, `comfort`, `comfort+`, `comfort-`).
  - Maximum boiler power step (`2`, `4`, `6`, `8` kW).
- **Track connectivity and DHW state**:
  - Online/offline connectivity status.
  - Dedicated domestic hot water entity with current and target temperature attributes.

## Installation (HACS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JanKrl&repository=ha-kospel-cmi&category=integration)

Manual HACS steps:

1. Open **HACS** -> **Integrations** -> **three-dot menu** -> **Custom repositories**.
2. Add repository URL: `https://github.com/JanKrl/ha-kospel-cmi`.
3. Category: **Integration**.
4. Install **Kospel Electric Heaters** from HACS.
5. Restart Home Assistant.
6. Go to **Settings** -> **Devices & Services** -> **Add Integration** -> **Kospel Electric Heaters**.

## First-Time Setup

When adding the integration in Home Assistant:

- Choose **Discover** to scan your network for compatible devices, or
- choose **Manual** and enter heater IP + device ID.

## Requirements

- Home Assistant `2024.1+` with support for custom integrations (HACS recommended).
- Your Home Assistant instance must be able to reach the heater in your local network.
- The integration works on older Home Assistant versions too; `2026.3+` only improves branding (custom icon/logo in UI).
- To show branded icons/logos on older Home Assistant versions, integration assets must be added to the [Home Assistant brands repository](https://github.com/home-assistant/brands).

## Supported Devices

- **EKCO.M3**.
- Want to add support for more models? Please contribute in [kospel-cmi-lib](https://github.com/JanKrl/kospel-cmi-lib).

## Entities

The integration creates the following entities in Home Assistant.
Entity IDs below are representative examples and can vary based on your device naming:

### Climate

- **Climate Entity**: `climate.heater`
  - **HVAC Modes**: `off`, `heat`, `auto`
  - **Preset Modes**: `winter`, `summer`, `party`, `vacation`
  - **Attributes**:
    - Current temperature (CH temperature)
    - Target temperature (in manual heat mode)

### Water Heater

- **Water Heater Entity**: `water_heater.domestic_hot_water`
  - **Purpose**: DHW state visualization
  - **Attributes**:
    - Current water temperature
    - Target DHW temperature

### Sensors

- **Temperature and Setpoint Sensors**:
  - `sensor.ch_temperature`
  - `sensor.dhw_temperature`
  - `sensor.ch_target_temperature`
  - `sensor.dhw_target_temperature`
- **System Sensors**:
  - `sensor.pressure`
  - `sensor.instant_power`
  - `sensor.boiler_max_power_limit`
- **Status Sensors**:
  - `sensor.ch_heating_status` (`running`, `idle`, `disabled`)
  - `sensor.dhw_heating_status` (`running`, `idle`, `disabled`)
  - `sensor.valve_position` (`CH`/`DHW`)

### Binary Sensors

- **Connectivity Sensor**:
  - `binary_sensor.connectivity`

### Number (Configuration)

- **Room Preset Temperature Entities**:
  - `number.eco`
  - `number.comfort`
  - `number.comfort_plus`
  - `number.comfort_minus`

### Select (Configuration)

- **Max Boiler Power Entity**:
  - `select.max_boiler_power`
  - Available options: `2 kW`, `4 kW`, `6 kW`, `8 kW`

## How To Use (Important Notes)

- **Climate target temperature** can be changed only in **Heat** (manual) HVAC mode.
- **Auto mode presets** are available as climate presets (`winter`, `summer`, `party`, `vacation`).
- **Auto mode schedules** can be read from the device state, but editing schedules from Home Assistant is not supported yet.
- **DHW water heater entity** is intentionally read-only for writes; it reflects device state.
- After changing values, refresh can be slightly delayed by design (configurable integration option).

## Troubleshooting

- If setup fails, verify heater IP/device ID and confirm Home Assistant can reach the heater on your LAN.
- If entities are unavailable, check Home Assistant logs for `custom_components.kospel` messages.
- For discovery issues, use manual IP + device ID setup path.
- If behavior looks wrong, open an issue with logs and your setup details.

## For Advanced Users

See [Advanced usage and technical notes](docs/advanced-usage.md) for:

- backend details (HTTP vs YAML mode),
- entity behavior details and known limitations,
- tuning options,
- development and test commands,
- architecture references.

## Feedback and Issues

- Bug reports and feature requests: [GitHub Issues](https://github.com/JanKrl/ha-kospel-cmi/issues)

## License

Apache License 2.0. See [LICENSE](LICENSE).
