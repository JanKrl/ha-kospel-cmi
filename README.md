# Kospel Electric Heaters for Home Assistant (Beta)

<p align="center">
  <img src="custom_components/kospel/brand/icon.png" alt="Kospel K-CMI" width="160" height="160">
</p>

Control and monitor compatible Kospel electric heaters from Home Assistant using local network communication.

> [!WARNING]
> This is a beta integration. Features and behavior may still change before stable release.

## What You Can Do

- Monitor heater and system values (room/water temperatures, pressure, power, heating status, valve position).
- Control core heating behavior from one climate entity (off/heat/auto + presets).
- Manage selected configuration values (room preset temperatures and max boiler power step).
- Expose DHW state in Home Assistant with a dedicated water heater entity.

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

## Entities Created

The integration creates these Home Assistant platforms:

- `climate` (main heater control)
- `water_heater` (DHW state and temperatures)
- `sensor` + `binary_sensor` (telemetry and status)
- `number` (room preset temperatures; configuration)
- `select` (boiler max power step; configuration)

## How To Use (Important Notes)

- **Climate target temperature** can be changed only in **Heat** (manual) HVAC mode.
- **Auto mode presets** are available as climate presets (`winter`, `summer`, `party`, `vacation`).
- **Auto mode schedules** can be read from the device state, but editing schedules from Home Assistant is not supported yet.
- **DHW water heater entity** is intentionally read-only for writes in this beta; it reflects device state.
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
