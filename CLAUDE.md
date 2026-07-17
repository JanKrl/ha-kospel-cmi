# CLAUDE.md — AI Agent Context for kospel-cmi-lib

This file provides structured context for Claude, Antigravity, GitHub Copilot, and other AI coding agents working on this repository. 

For full technical and development specs, this file delegates to the Single Source of Truth (SSOT) documents in the `docs/` folder.

---

## Project Identity

- **Name**: kospel-cmi-lib
- **Type**: Python library (HTTP client)
- **Purpose**: Control Kospel C.MI electric heaters via local HTTP REST API
- **License**: Apache 2.0
- **Owner**: @JanKrl
- **Repository**: https://github.com/JanKrl/kospel-cmi-lib

## Architecture Overview

This library follows a strict **3-layer architecture**:

1. **Controller Layer (`EkcoM3`)**: High-level pythonic properties and async setters.
2. **Backend Protocol (`RegisterBackend`)**: Abstraction for register operations (`read_register`, `read_registers`, `write_register`). No transport details here.
3. **Transport Layer (`HttpRegisterBackend` / `YamlRegisterBackend`)**: Implements the protocol. The HTTP backend hits the physical heater; the YAML backend reads/writes a local `.yaml` file for simulator testing.

> [!IMPORTANT]
> **SSOT Pointer**: See [`docs/architecture.md`](docs/architecture.md) for architecture diagrams and deeper conceptual explanations of this 3-layer design.

## File Map

| Path | Purpose |
|------|---------|
| `src/kospel_cmi/controller/` | `EkcoM3` class and high-level Python API. |
| `src/kospel_cmi/kospel/` | `api.py` (HTTP transport), `simulator.py` (YAML transport), `backend.py` (Protocol definition), `discovery.py`. |
| `src/kospel_cmi/registers/` | Core register encoding/decoding, bit-flag manipulation, Enums. |
| `src/kospel_cmi/tools/` | CLI utilities (`kospel-discover`, `kospel-scan-registers`, `kospel-scan-live`). |
| `tests/` | Pytest suite. `conftest.py` has mock backends. `test_ekcom3.py` for integration. |

## Key Conventions & Constraints

1. **Async-first**: All I/O is asynchronous (`aiohttp`, `aiofiles`). Do not use `requests` or synchronous `open()`.
2. **Immediate Writes**: When calling `await controller.set_heater_mode(...)`, it immediately encodes the value and calls `backend.write_register`. There is no batch saving or delayed write.
3. **Read-Modify-Write**: Flag registers (multiple boolean flags in one 16-bit register) must be read first, mutated at the bit level, and written back. This is handled by `write_flag_bit(backend, ...)`.
4. **Strict Relative Imports**: If this library is vendored/embedded into Home Assistant custom components, absolute imports (like `from kospel_cmi...`) will break. You MUST follow the import rules below.

> [!CAUTION]
> **HACS Embedding Requirement**:
> When modifying this library to run within a Home Assistant integration context (e.g. `ha-kospel-cmi`), use ONLY relative imports inside the package. For example, `from .kospel.backend import...` instead of `from kospel_cmi.kospel.backend import...`.

## SSOT Pointers (Where to Look)

Do not guess formatting or standards. Consult the human-readable docs:

- **Register Encoding & Data Formats**: Read [`docs/technical.md`](docs/technical.md).
- **HTTP API specifics**: Read [`docs/technical.md`](docs/technical.md).
- **Adding New Settings / Workflow**: Read [`docs/development.md`](docs/development.md).
- **Testing & Style Standards**: Read [`docs/development.md`](docs/development.md).

## Common Pitfalls

1. **Bypassing the Protocol**: Do not make HTTP calls directly from the Controller. Always use the injected `self._backend.read_register()`.
2. **Checking Enum Validity**: Always use Enums in the Controller (e.g., `HeaterMode.WINTER`).
3. **`simulation_mode` flag**: There is NO `simulation_mode` flag in the code. Simulation is achieved purely by passing a `YamlRegisterBackend` to the `EkcoM3` constructor.
4. **Writing without waiting**: Forgetting `await` on register writes will lead to silent failures.
