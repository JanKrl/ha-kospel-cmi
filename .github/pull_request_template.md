## 🎯 Product Value & Goal
<!-- What user problem does this solve or what feature does it add? Keep it high-level. -->

## 🔗 Related Issues
<!-- Link related issues with "Relates to #123" (NOT Fixes) so they stay open until release. -->

## 🛠️ Technical Summary
<!-- Briefly describe the architectural approach. What trade-offs or compromises were made? Any tech debt introduced? -->

## 🧪 How to Verify
<!-- As a PO, how can I manually test this in Home Assistant or using the CLI? Provide clear steps. -->

## ✅ Release Checklist
- [ ] **Package boundary respected**: Changes are isolated to ONLY `lib/` OR `custom_components/kospel/` (never both).
- [ ] **Documentation**: `README.md` (and `lib/README.md` if applicable) is updated to reflect new features/changes.
- [ ] **Translation keys**: Added to `strings.json` and `translations/pl.json` (if new entities/UI strings).
- [ ] **Tests pass**: Automated tests pass (`uv run python -m pytest tests/ -v`).
- [ ] **Code conventions**: Follows guidelines in `.agents/AGENTS.md` (e.g. type hints, English code identifiers).
