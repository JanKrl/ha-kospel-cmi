# Publishing to GitHub and HACS

This document lists what is required to publish the repository to GitHub and make it installable via HACS.

## Already done in this repo

- **hacs.json** in repo root (name, `content_in_root: false`, `homeassistant`, `persistent_directory: "data"`).
- **manifest.json** has correct `documentation`, `issue_tracker`, and `codeowners` for `https://github.com/JanKrl/ha-kospel-cmi`.
- **README.md** includes HACS installation steps and license (Apache-2.0).
- **LICENSE** (Apache-2.0) is present.
- **pyproject.toml** has `urls = { Repository = "https://github.com/JanKrl/ha-kospel-cmi" }`.

## Steps on GitHub (after push)

1. **Repository description**  
   In repo **Settings** → **General** → **Description**, set a short description (e.g. “Home Assistant integration for Kospel electric heaters”). HACS uses this in the UI.

2. **Topics**  
   In **About** → **Topics**, add at least: `home-assistant`, `hacs`, `kospel`, `heater`, `integration`. Improves search in the HACS store.

3. **Releases (recommended)**  
   Create a **Release** (e.g. tag `v0.1.0`) so HACS can show version selection. Tag + release is required for that; a bare tag is not enough.

## HACS: custom repository (user install)

Users add the repo as a custom repository in HACS:

1. HACS → **Integrations** → **⋮** → **Custom repositories**.
2. URL: `https://github.com/JanKrl/ha-kospel-cmi`, type **Integration** → **Add**.
3. Search “Kospel Electric Heaters” and install.

No approval is needed for custom repos; the above is enough.

## Optional: default HACS store

To have the integration listed in the default HACS store (without adding a custom repo), you must:

1. **Home Assistant Brands**  
   Add the integration to [home-assistant/brands](https://github.com/home-assistant/brands) so it follows HA UI standards (icons, etc.). See [Brands documentation](https://developers.home-assistant.io/docs/creating_integration_manifest/#brands).

2. **HACS default repositories**  
   Follow [Include default repositories](https://hacs.xyz/docs/publish/include/) and submit a pull request to the HACS default list.

## pyproject.toml note

`requires-python = ">=3.14"` is set in pyproject.toml. Home Assistant currently runs on Python 3.11/3.12. If this package is only used inside Home Assistant, consider `requires-python = ">=3.11"` so it aligns with HA’s supported versions.
