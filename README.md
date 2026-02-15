# Kospel Heater Home Assistant Integration

Home Assistant integration for Kospel electric heaters. Control your heater via climate entity, sensors, and switches.

> **⚠️ Development version**  
> This integration is **not ready for production use**. It is under active development and may contain bugs, incomplete features, or breaking changes. Install only if you want to test and provide feedback.

## What it does

- **Climate entity** – Set heating mode (Summer/Winter/Off), target temperature
- **Sensors** – Room temperature, water temperature, pressure, pump status, valve position
- **Switches** – Manual mode, water heater on/off

## Installation (HACS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JanKrl&repository=ha-kospel-cmi&category=integration)

If your Home Assistant instance is [linked to My Home Assistant](https://my.home-assistant.io/), click the badge above to open this repository in HACS. Otherwise add the repo manually:

1. In HACS go to **Integrations** → **⋮** → **Custom repositories**
2. Add: `https://github.com/JanKrl/ha-kospel-cmi`
3. Select **Integration** and click **Add**
4. Search **Kospel Electric Heaters**, install, restart Home Assistant
5. **Settings** → **Devices & services** → **Add integration** → **Kospel Electric Heaters**

When configuring, choose:
- **Heater (HTTP)** – Connect to your heater (IP address + device ID)
- **File-based (development)** – Test without hardware; state stored in a YAML file

See [INSTALLATION.md](INSTALLATION.md) for manual installation and troubleshooting.

## Requirements

- Home Assistant 2024.1 or later
- Kospel heater on your network (for real device) or use File-based mode for testing

## License

Apache License 2.0. See [LICENSE](LICENSE).
