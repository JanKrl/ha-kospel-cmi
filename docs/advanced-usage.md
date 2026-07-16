# Advanced Usage and Technical Notes

This page is for users who want deeper control, better diagnostics, or development context.

## Backend Modes

### HTTP backend (real heater)

- Connects to a real Kospel module over LAN.
- Uses heater IP and device ID selected in config flow.
- Best choice for normal Home Assistant usage.
- Note: MAC-based auto-discovery is currently hidden/disabled in UI due to
  unresolved MAC-prefix mismatch observed on a real device. Network scan and
  manual entry are the supported setup paths until discovery matching is revised.

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
- `number` entities also expose DHW preset temperatures:
  - economy, comfort
- `number` entity exposes the outside temperature switch-off threshold:
  - When outside temperature exceeds this threshold, the heater turns off.
- `select` entity exposes boiler max power step:
  - power steps are dynamically discovered based on the connected device hardware configuration.

### Heating status sensors (deprecated)

The individual CH and DHW heating status sensors (`sensor.ch_heating`, `sensor.dhw_heating`) are **deprecated** and will be removed in v1.0.0.

Use the combined **Heating mode** sensor (`sensor.heating_mode`) instead, which reports a single state: `off`, `idle`, `ch`, or `dwh`. Since CH and DHW heating can never run simultaneously by design, this combined sensor is more useful.

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
