# Kospel HTTP API

This module implements HTTP communication with the Kospel C.MI heater device.

## API Endpoints

**Base URL**: `http://<HEATER_IP>/api/dev/<DEVICE_ID>`

### Read Register

Read a single register from the heater.

- **Endpoint**: `GET /api/dev/<DEVICE_ID>/<register>/<count>`
- **Example**: `GET /api/dev/65/0b55/1`
- **Response**: `{"regs": {"0b55": "d700"}, "sn": "...", "time": "..."}`

### Write Register

Write a register value to the heater.

- **Endpoint**: `POST /api/dev/<DEVICE_ID>/<register>`
- **Body**: Hex string (e.g., `"d700"`)
- **Content-Type**: `application/json`
- **Response**: `{"status": "0"}` on success (0 = success)

### Read Multiple Registers

Read multiple registers in a single request.

- **Endpoint**: `GET /api/dev/<DEVICE_ID>/<start_register>/<count>`
- **Example**: `GET /api/dev/65/0b00/256` (reads 256 registers starting from 0b00)
- **Response**: `{"regs": {"0b00": "...", "0b01": "...", ...}}`

## Request/Response Format

- All register values are hex strings (4 characters)
- Values use little-endian byte order
- JSON encoding for requests and responses

## Error Handling

**Network Errors**:
- Timeout: 5 seconds (configurable)
- Connection errors: Returns `None` or empty dict
- HTTP errors: Logged and returns `None`/`False`

## Device Discovery

Probe a host to verify it is a Kospel C.MI device and obtain device list (no device_id required):

- **Endpoint**: `GET /api/dev`
- **Response**: `{"status": "0", "sn": "mi01_...", "devs": ["65"]}`

Optionally fetch per-device info:

- **Endpoint**: `GET /api/dev/<DEVICE_ID>/info`
- **Response**: `{"status": "0", "info": {"id": 19, "moduleID": "65", ...}}`

**Model ID mapping** (from Kospel web UI):
- 18: EKD.M3 (kocioł dwufunkcyjny)
- 19: EKCO.M3 (kocioł elektryczny)
- 65: C.MG3 (moduł obiegów)
- 81: C.MW3 (pompa ciepła)

**Usage**:

```python
import aiohttp
from kospel_cmi import probe_device, discover_devices

async with aiohttp.ClientSession() as session:
    info = await probe_device(session, "192.168.101.49")
    if info:
        print(info.serial_number, info.device_ids, info.devices[0].model_name)

    found = await discover_devices(session, "192.168.101.0/24")
    for device in found:
        print(device.host, device.serial_number)
```

## Implementation

The HTTP API is implemented in:
- `api.py` - Low-level HTTP functions (`read_register`, `read_registers`, `write_register`)
- `backend.py` - `HttpRegisterBackend` class that implements the `RegisterBackend` protocol
- `discovery.py` - Device probe and network discovery (`probe_device`, `discover_devices`)

## References

This library was reverse-engineered from JavaScript code used in the heater's web interface. Key findings:

- Register encoding uses little-endian byte order
- Flag bits are used for boolean settings within registers
- Temperature and pressure values are scaled for precision
- Read-Modify-Write pattern is required for setting flag bits

For details on register encoding and decoding, see [`../registers/README.md`](../registers/README.md).
