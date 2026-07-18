# Documentation Index

Project documentation for kospel-cmi-lib.

## Project Documentation

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design, layers, components, and data flow |
| [Technical Specs](technical.md) | Implementation details, data formats, protocols, testing, and coding standards |
| [Development Guide](development.md) | Contributing, adding settings, and testing |
| [Register Mapping (UI Analysis)](register_mapping_from_ui.md) | Reverse-engineering reference from manufacturer web UI (Polish) |

## Module Documentation

Module-specific documentation is co-located with the code:

- [kospel/](../src/kospel_cmi/kospel/README.md) — HTTP API endpoints, backends, and device discovery
- [registers/](../src/kospel_cmi/registers/README.md) — Register encoding, decoding, and mappings
- [controller/](../src/kospel_cmi/controller/README.md) — EkcoM3 device class
- [tools/](../src/kospel_cmi/tools/README.md) — Register scanner, live scanner, and discovery CLI

## Suggested Reading Order

**For contributors:**

1. [Architecture](architecture.md) — Understand system design and layer boundaries
2. [Technical Specs](technical.md) — Data formats, protocols, and coding standards
3. [Development Guide](development.md) — How to add settings and run tests

**For users:**

1. [README](../README.md) — Installation and usage
2. [controller/README](../src/kospel_cmi/controller/README.md) — Registry and helper methods
3. [kospel/README](../src/kospel_cmi/kospel/README.md) — HTTP API and discovery
