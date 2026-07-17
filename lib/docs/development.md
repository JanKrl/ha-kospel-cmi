# Development Guide

This guide is for contributors and developers working on the kospel-cmi-lib project.

## Adding New Settings

To add a new setting to `EkcoM3`:

### 1. Add property (read-only or read-write)

In `src/kospel_cmi/controller/device.py`:

**Read-only (e.g. sensor):**
```python
@property
def new_sensor(self) -> Optional[float]:
    """New sensor description."""
    return decode_scaled_x10(self._get_register("0bXX"))
```

**Writable:**
```python
@property
def new_setting(self) -> Optional[float]:
    """New setting description."""
    return decode_scaled_x10(self._get_register("0bXX"))

async def set_new_setting(self, value: float) -> bool:
    """Set new setting (0bXX)."""
    return await self._set_scaled_x10("0bXX", value)
```

### 2. Add decoder/encoder (if new type)

If the setting uses a **new** decode/encode type, add it to `registers/decoders.py` and `registers/encoders.py`. For existing types (`scaled_x10`, `scaled_x100`, `heater_mode`, `decode_map`/`encode_map`), reuse them.

### 3. Add enum (if needed)

Add an enum in `src/kospel_cmi/registers/enums.py` and use it in decode_map/encode_map for bit-flag settings.

For more details, see [`../src/kospel_cmi/controller/README.md`](../src/kospel_cmi/controller/README.md).

## Best Practices

- **Use high-level API**: Prefer `EkcoM3` (properties and setters) over direct register manipulation
- **Immediate writes**: Each `set_*()` writes immediately; no batching
- **Avoid redundant calls**: Use `from_registers()` when you already have register data
- **Error handling**: Check return values and handle `None` results appropriately
- **Simulator mode**: Use YAML backend for development and testing

## Testing

Automated tests are defined using `pytest` framework. After every set of changes, tests must be run to verify that the library works as expected.

### Test Organization

All tests are defined in `tests/` directory.

### Testing Principles

1. **TDD Approach**: Write tests before or alongside implementation
2. **Layer Isolation**: Test each layer independently
3. **Mock External I/O**: Mock HTTP requests/responses
4. **Coverage Target**: ≥80% code coverage
5. **Async Testing**: Use `pytest-asyncio` for async functions

### Test Types

**Unit Tests**:
- Test individual functions in isolation
- Mock external dependencies
- Test edge cases and error conditions

**Integration Tests**:
- Test cross-layer functionality
- Use mock HTTP responses
- Test end-to-end workflows

**Simulator Mode Tests**:
- Simulator tests should only verify if the simulator itself works as expected
- No end-to-end tests should be defined for cases with and without the simulator

### Running Tests

```bash
# Install test dependencies
uv sync --group dev

# Run all tests
pytest

# Run with coverage
pytest --cov=src/kospel_cmi --cov-report=html
```

## Code Style and Standards

### Type Hinting

- **Strict Typing**: All functions must have complete type hints
- **No Any**: Avoid `Any` type unless absolutely necessary
- **Protocol Types**: Use for structural typing
- **Optional Returns**: Use `Optional[T]` for nullable returns

### Documentation

- **Google-style Docstrings**: All public classes and methods
- **Parameter Documentation**: Document all parameters and return values
- **Example Usage**: Include examples where helpful
- **Comments and docstrings**: Explain *why*, not *what*

### Error Handling

- **Explicit Handling**: Never pass exceptions silently
- **Custom Exceptions**: Use `kospel_cmi.exceptions` (`KospelConnectionError`, `RegisterMissingError`, `RegisterValueInvalidError`, `IncompleteRegisterRefreshError`, `KospelWriteError`, etc.)
- **Logging**: Log errors with context
- **HTTP/Simulator writes**: Raise on failure; do not use boolean success returns for writes

### Code Style

- **PEP 8**: Follow Python style guide
- **Ruff**: Automated linting and formatting
- **Line Length**: 88 characters (Black-compatible)
- **Import Organization**: Standard library → third-party → local

## Architecture

See [`architecture.md`](architecture.md) for system architecture and design patterns.
