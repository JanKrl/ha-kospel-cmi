# Advanced Usage and Technical Notes

This page is for users who want deeper control, better diagnostics, or development context.

## Backend Modes

### HTTP backend (real heater)

- Connects to a real Kospel module over LAN.
- Uses heater IP and device ID selected in config flow.
- Best choice for normal Home Assistant usage.

### YAML backend (development mode)

- No heater required.
- Stores register state in local file:
  - `custom_components/kospel/data/state.yaml`
- Intended for development/testing only.

## Entity Behavior Details

### Climate entity

- Home Assistant modes map to heater modes:
  - `off` -> heater off
  - `heat` -> manual mode
  - `auto` -> automatic program mode
- Climate presets map to heater auto programs:
  - `winter`, `summer`, `party`, `vacation`
- Target temperature writes are accepted only in `heat` mode.

### DHW water heater entity

- Exposes DHW current temperature, target temperature, and operation state.
- Write actions on this entity are currently ignored by design in beta.
- DHW behavior is driven by heater state and climate/program context.

### Configuration entities

- `number` entities expose room preset temperatures:
  - economy, comfort, comfort+, comfort-
- `select` entity exposes boiler max power step:
  - power steps are device-specific,
  - `2`, `4`, `6`, `8` kW steps are for **EKCO.M3**.

## Tuning

You can set post-write refresh delay in integration options:

- Open integration -> **Configure**.
- Adjust `refresh_delay_after_set` (seconds).
- This delay controls how long Home Assistant waits before refreshing after writes.

## Troubleshooting and Diagnostics

- Main integration logger: `custom_components.kospel`
- For setup issues:
  - verify heater IP is reachable from Home Assistant host,
  - verify correct device ID,
  - confirm the heater module is online.
- For unavailable entities:
  - inspect Home Assistant logs around coordinator refresh failures.

## Architecture and Development References

- Integration architecture: [architecture.md](architecture.md)
- Technical specification: [technical.md](technical.md)

### Local test command

```bash
uv sync --all-groups
uv run python -m pytest tests/ -v
```
