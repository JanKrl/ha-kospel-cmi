# Device Controller

`EkcoM3` is a device-specific class for the Kospel C.MI Standard heater.
All settings and sensors are explicit properties; writes happen immediately (no `save()`).

## Usage

```python
from kospel_cmi.controller.device import EkcoM3
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend

# Create device with backend (optional strict_refresh=True for atomic snapshots)
backend = HttpRegisterBackend(session, api_base_url)
controller = EkcoM3(backend=backend)

# Refresh register data
await controller.refresh()

# Read properties
mode = controller.heater_mode
temp = controller.room_temperature

# Write (immediate; no save())
await controller.set_heater_mode(HeaterMode.WINTER)
await controller.set_manual_temperature(22.0)

# Helper methods
await controller.set_manual_heating(22.0)  # MANUAL mode + temperature
await controller.set_water_mode(CwuMode.COMFORT)
await controller.set_water_comfort_temperature(38.0)
```

## Properties (read-only)

- `heater_mode`, `manual_temperature`, `room_temperature`, `room_setpoint`
- `cwu_mode`, `cwu_temperature_economy`, `cwu_temperature_comfort`
- `is_water_heater_enabled`, `is_co_heating_active`, `is_cwu_heating_active`
- `co_heating_status`, `cwu_heating_status` (computed)
- `pressure`, `power` (0b46, delivered kW), `flow`, `valve_position`, etc.
- `boiler_max_power_index` (0b62), `boiler_max_power_kw` (0b34, limit in kW; not written by this library—refresh after changing index)

## Async setters (write immediately)

- `set_heater_mode(value)` — writes 0b55; if MANUAL also writes 0b32
- `set_manual_temperature(value)` — writes 0b8d
- `set_boiler_max_power_index(value)` — writes 0b62 only; firmware updates 0b34
- `set_room_mode(value)`, `set_cwu_mode(value)`
- `set_is_water_heater_enabled(value)`
- `set_room_temperature_*`, `set_cwu_temperature_*`, etc.

## Helper methods

- `set_manual_heating(temperature)` — MANUAL mode + target temperature
- `set_water_mode(mode: CwuMode)` — CWU mode (ECONOMY, ANTI_FREEZE, COMFORT)
- `set_water_comfort_temperature(temperature)` — CWU comfort temp only
- `set_water_economy_temperature(temperature)` — CWU economy temp only

## Refresh modes

- **Default (`strict_refresh=False`)**: After `refresh()`, the cache holds whatever the batch returned (possibly incomplete). Missing keys surface as `RegisterMissingError` when reading a property.
- **Strict (`strict_refresh=True`)**: After `refresh()`, either the cache is fully replaced with a batch that contains every address in **`EkcoM3.REQUIRED_REGISTERS`**, or **`IncompleteRegisterRefreshError`** is raised and the **previous cache is unchanged**.

`REQUIRED_REGISTERS` is defined on the class and covers all public read-only properties. When adding a new read property, add its register address(es) to that set (see `device.py`).

**Home Assistant:** Use `strict_refresh=True` and map `IncompleteRegisterRefreshError` to `UpdateFailed` in your data update coordinator so a bad partial snapshot does not leave entities in a misleading “available” state.
