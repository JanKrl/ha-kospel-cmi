# AI Agent Context

You are working in `kospel-cmi-lib`, a Python HTTP client library for Kospel electric heaters. 

Please read the `CLAUDE.md` file in the root of the repository. It serves as the primary context index for AI agents like you. 

Key reminders:
1. We use a strict 3-layer architecture (`EkcoM3` Controller -> `RegisterBackend` Protocol -> `Http/Yaml` Backends).
2. All I/O is asynchronous.
3. The project delegates coding standards, testing instructions, and data format specs to the `docs/` folder. Please refer to `docs/development.md` for coding standards and `docs/technical.md` for API specs.
4. If writing code that will be used inside Home Assistant (HACS), ensure you use relative imports within `src/kospel_cmi`.
