# Kospel Electric Heaters for Home Assistant

<p align="center">
  <img src="custom_components/kospel/brand/icon.png" alt="Kospel K-CMI" width="160" height="160">
</p>

Control and monitor compatible Kospel electric heaters from Home Assistant using local network communication.

[![Buy me a coffee](https://img.shields.io/badge/Kup%20mi%20kaw%C4%99-buycoffee.to-ffdd00.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buycoffee.to/jankrl)


> [!WARNING]
> This is an unofficial, community-maintained integration and is not affiliated with or endorsed by Kospel.
> Use it at your own responsibility.

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
  - **Modes**: Controlled by climate preset modes
  - **Attributes**:
    - Current water temperature
    - Target DHW temperature

### Sensors

- **Temperature and Setpoint Sensors**:
  - Central heating (CH) current temperature
  - Domestic water heating (DWH) current temperature
  - CH target temperature
  - DWH target temperature
  - Outside temperature
- **System Sensors**:
  - System pressure
  - Current power consumption
  - Valve position CO / DWH
  - Heating mode CO / DWH

### Binary Sensors

- **Connectivity Sensor**:
  - Connectivity

### Number (Configuration)

- **Room Preset Temperature Entities**:
  - Economy
  - Comfort
  - Comfort+
  - Comfort-
- **DHW Preset Temperature Entities**:
  - Eco
  - Comfort
- **Limit Entities**:
  - Outside temperature switch threshold

### Select (Configuration)

- **Max Boiler Power Entity**:
  - Limit device power to: `2 kW`, `4 kW`, `6 kW`, `8 kW`

## Custom Lovelace Cards

The integration includes two custom Home Assistant dashboard cards that are automatically loaded into your Lovelace UI:

1. **`kospel-program-card` (Daily Program Editor)**:
   - Visually edit 8 Daily Programs for Central Heating (CH), Domestic Hot Water (DHW), and Circulation.
   - 24-hour color-coded timeline preview with up to 5 time slots per program.
   - Interactive time pickers (`HH:MM`) and preset selectors (`Antifreeze`, `Economy`, `Comfort`, `Comfort+`, `Eco`, `On`, etc.).
   - Action buttons to load and save daily programs via integration services.

2. **`kospel-weekday-card` (Weekday Schedule Assignment)**:
   - Assign Daily Programs 1–8 to each day of the week (Monday through Sunday).
   - Action buttons to load and save weekday schedules.

### Example Dashboard YAML Setup

```yaml
type: custom:kospel-program-card
title: Daily Program Editor
schedule_type: ch
program_id: 1
```

```yaml
type: custom:kospel-weekday-card
title: Weekday Heating Schedule
schedule_type: ch
```

## How To Use (Important Notes)

- **Climate target temperature** can be changed only in **Heat** (manual) HVAC mode.
- **Auto mode presets** are available as climate presets (`winter`, `summer`, `party`, `vacation`).
- **Auto mode schedules** can be viewed and configured visually using the custom Lovelace cards (`kospel-program-card` and `kospel-weekday-card`) or via services (`kospel.set_program`, `kospel.set_weekday_schedule`).
- **DHW water heater entity** is intentionally read-only for writes; it reflects device state.
- After changing values, refresh can be slightly delayed by design (configurable integration option).

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

For contributors, see [CONTRIBUTING.md](CONTRIBUTING.md).
For AI coding agents (Claude, Antigravity, etc.), see [AGENTS.md](.agents/AGENTS.md).

## Feedback and Issues

- Bug reports and feature requests: [GitHub Issues](https://github.com/JanKrl/ha-kospel-cmi/issues)

## Support / Wsparcie

☕ **Enjoying this integration? / Podoba Ci się ta integracja?**  
I maintain this open-source integration in my private time. If you'd like to say thanks with a coffee / Rozwijam ten projekt w wolnym czasie — jeśli chcesz podziękować kawą ☕: [buycoffee.to/jankrl](https://buycoffee.to/jankrl)


## License

Apache License 2.0. See [LICENSE](LICENSE).

