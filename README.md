# Kospel Electric Heaters for Home Assistant

<p align="center">
  <img src="custom_components/kospel/brand/icon.png" alt="Kospel K-CMI" width="160" height="160">
</p>

Control and monitor compatible Kospel electric heaters and instantaneous water heaters from Home Assistant using local network communication.

[![Buy me a coffee](https://img.shields.io/badge/Kup%20mi%20kaw%C4%99-buycoffee.to-ffdd00.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buycoffee.to/jankrl)


> [!WARNING]
> This is an unofficial, community-maintained integration and is not affiliated with or endorsed by Kospel.
> Use it at your own responsibility.

## Supported Devices

- **EKCO.M3** (Central heating & DHW boiler via Kospel **C.MI** module)
- **PPE.4** (Instantaneous water heater with built-in Wi-Fi / ModBus-over-HTTP)
- Want to add support for more models? Please contribute in [kospel-cmi-lib](https://github.com/JanKrl/ha-kospel-cmi).

## Entities

The integration creates entities tailored to the connected Kospel device.
Entity IDs below are representative examples and can vary based on your device naming:

### Climate (`EKCO.M3`)

- **Climate Entity**: `climate.heater`
  - **HVAC Modes**: `off`, `heat`, `auto`
  - **Preset Modes**: `winter`, `summer`, `party`, `vacation`
  - **Attributes**:
    - Current temperature (CH temperature)
    - Target temperature (in manual heat mode)

### Water Heater (`EKCO.M3` & `PPE.4`)

- **Water Heater Entity**: `water_heater.domestic_hot_water`
  - **`EKCO.M3`**: Read-only status reflecting device DHW temperature, supply setpoint, and operation mode (`eco`, `performance`, `off`) driven by the climate entity.
  - **`PPE.4`**: Full read/write control of target water temperature (`20°C` up to device temperature lock limit) and active operation mode (`manual`, `profile_1`, `profile_2`, `profile_3`).

### Sensors

- **Temperature and Setpoint Sensors**:
  - Central heating (CH) current & target temperatures (`EKCO.M3`)
  - Domestic hot water (DHW) current & target temperatures (`EKCO.M3`)
  - Outside temperature (`EKCO.M3`)
  - Return (inlet) & supply (outlet) temperatures (`EKCO.M3`, `PPE.4`)
  - Internal electronics temperature (`PPE.4`, diagnostic)
- **System & Consumption Sensors**:
  - System pressure (`EKCO.M3`)
  - Water flow rate (`EKCO.M3`, `PPE.4`)
  - Instantaneous power consumption (`EKCO.M3`, `PPE.4`)
  - Max power limit (`EKCO.M3`, `PPE.4`) and installed power (`PPE.4`)
  - Daily energy consumption in kWh (`PPE.4`, Energy Dashboard compatible)
  - Daily water consumption in L (`PPE.4`, Energy Dashboard compatible)
  - Valve position CH / DHW (`EKCO.M3`)
  - Heating mode CH / DHW (`EKCO.M3`)

### Binary Sensors

- **Connectivity Sensor**:
  - Connectivity (`EKCO.M3`, `PPE.4`)

### Number (Configuration)

- **Room Preset Temperature Entities (`EKCO.M3`)**:
  - Economy, Comfort, Comfort+, Comfort−
- **DHW Preset Temperature Entities (`EKCO.M3`)**:
  - Eco, Comfort
- **Limit Entities (`EKCO.M3`)**:
  - Outside temperature switch threshold
- **Profile Temperature Entities (`PPE.4`)**:
  - Profile 1, Profile 2, Profile 3 target temperatures

### Select (Configuration)

- **Max Boiler Power Entity (`EKCO.M3`)**:
  - Limit device power to: `2 kW`, `4 kW`, `6 kW`, `8 kW`

## How To Use (Important Notes)

- **`EKCO.M3`**:
  - **Climate target temperature** can be changed only in **Heat** (manual) HVAC mode.
  - **Auto mode presets** are available as climate presets (`winter`, `summer`, `party`, `vacation`).
  - **DHW water heater entity** is intentionally read-only for writes; it reflects device state.
- **`PPE.4`**:
  - Setting a target temperature on the **Water Heater** entity automatically switches the heater to `manual` mode at the chosen temperature.
  - Selecting `profile_1`, `profile_2`, or `profile_3` operation mode activates the corresponding preset profile.
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

- Choose **Discover** to scan your network for compatible devices (both C.MI and built-in Wi-Fi / ModBus heaters), or
- choose **Manual**, select your connection type (**C.MI Module** or **Built-in Wi-Fi (ModBus)**), and enter the heater IP, device model, and (for C.MI) device ID.

## Requirements

- Home Assistant `2024.1+` with support for custom integrations (HACS recommended).
- Your Home Assistant instance must be able to reach the heater in your local network.
- The integration works on older Home Assistant versions too; `2026.3+` only improves branding (custom icon/logo in UI).
- To show branded icons/logos on older Home Assistant versions, integration assets must be added to the [Home Assistant brands repository](https://github.com/home-assistant/brands).

## Troubleshooting

- If setup fails, verify heater IP/device ID and confirm Home Assistant can reach the heater on your LAN.
- If entities are unavailable, check Home Assistant logs for `custom_components.kospel` messages.
- For discovery issues, use the manual setup path.
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
