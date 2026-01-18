# Cleanup Procedures

## Purpose
This document provides procedures for cleaning up after test execution and resetting the test environment.

---

## Post-Test Session Cleanup

### 1. Save Test Artifacts

Before cleaning up, ensure all test artifacts are saved:

| Artifact | Location | Action |
|----------|----------|--------|
| Test session log | `results/` | Move to permanent storage |
| Bug reports | `results/` | Move to permanent storage |
| Screenshots | `results/` | Archive with session |
| Log files | Home Assistant logs | Export relevant sections |
| State file backup | `data/` | Archive if useful |

### 2. Document Final State

Record the final state of the test environment:

```
Final State Documentation
=========================

Date: ____________
Session ID: ____________

Integration Status: [ ] Installed / [ ] Removed
State File: [ ] Present / [ ] Deleted
Environment Variables: [ ] Set / [ ] Cleared

Entity States:
- Climate Mode: ____________
- Manual Mode: ____________
- Water Heater: ____________
- Manual Temp: ____________

Notes: ____________
```

---

## Reset Procedures

### Reset Simulator State

To reset simulator state to defaults:

1. Stop Home Assistant (optional but recommended)
2. Edit or replace state file:

```bash
# Option A: Delete and let integration recreate
rm <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml

# Option B: Replace with known-good state
cat > <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml << 'EOF'
"0b51": "0000"
"0b55": "0020"
"0b66": "9001"
"0b67": "a401"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b8a": "f401"
"0b8d": "e100"
EOF
```

3. Restart Home Assistant

### Reset Integration Configuration

To remove and re-add the integration:

1. Navigate to Settings > Devices & Services
2. Click on Kospel Electric Heaters integration
3. Click three-dot menu > Delete
4. Confirm deletion
5. Verify integration removed from list
6. Click Add Integration
7. Search for "Kospel Electric Heaters"
8. Complete configuration

### Full Environment Reset

For a complete reset:

1. Remove integration (see above)
2. Stop Home Assistant
3. Delete integration files:
```bash
rm -rf <HA_CONFIG>/custom_components/kospel
```
4. Re-copy fresh integration files
5. Delete any cached data
6. Start Home Assistant
7. Configure integration fresh

---

## State File Management

### Backup State File

```bash
cp <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml \
   <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml.backup
```

### Restore State File

```bash
cp <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml.backup \
   <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
```

### Standard Test State Files

#### Minimal State (Empty System)
```yaml
"0b51": "0000"
"0b55": "0000"
"0b8a": "0000"
```

#### Winter Mode Active
```yaml
"0b51": "0000"
"0b55": "0020"
"0b66": "9001"
"0b67": "a401"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b8a": "f401"
"0b8d": "e100"
```

#### Summer Mode Active
```yaml
"0b51": "0000"
"0b55": "0008"
"0b66": "9001"
"0b67": "a401"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b8a": "f401"
"0b8d": "e100"
```

#### All Features Active
```yaml
"0b51": "0700"
"0b55": "0230"
"0b66": "9001"
"0b67": "a401"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b8a": "f401"
"0b8d": "e100"
```

---

## Log Cleanup

### Export Relevant Logs

Before clearing logs, export test-related entries:

1. Navigate to Settings > System > Logs
2. Click "Download full log"
3. Save with session ID: `logs_session_YYYYMMDD_HHMMSS.txt`

### Filter Kospel Logs

```bash
# Extract Kospel-related log entries
grep -i kospel home-assistant.log > kospel_logs_session.txt
```

### Clear Debug Logging

After testing, revert to standard logging:

Edit `configuration.yaml`:
```yaml
logger:
  default: info
  # Remove or comment out Kospel debug entries
  # logs:
  #   custom_components.kospel: debug
```

Restart Home Assistant to apply.

---

## Environment Variable Cleanup

If you want to disable simulation mode:

### Docker Compose
```yaml
environment:
  # - SIMULATION_MODE=1  # Comment out
```

### Docker Run
Remove `-e SIMULATION_MODE=1` from command

### Shell
```bash
unset SIMULATION_MODE
```

### Systemd
Remove `Environment=SIMULATION_MODE=1` from service file

---

## Cleanup Checklist

Use this checklist after each test session:

### Test Artifacts
- [ ] Test session log completed and saved
- [ ] Bug reports created and saved
- [ ] Screenshots archived
- [ ] Log excerpts exported

### Environment State
- [ ] Decision made: Keep or reset state file
- [ ] Integration state documented
- [ ] Any temporary changes reverted

### For Next Session
- [ ] State file ready for next tests
- [ ] Integration in known state
- [ ] Environment variables still set (if needed)

---

## Troubleshooting Cleanup Issues

### Can't Delete State File

```bash
# Check permissions
ls -la <HA_CONFIG>/custom_components/kospel/data/

# Fix permissions if needed
chmod 644 <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
```

### Integration Won't Remove

1. Try from Developer Tools > Services
2. Call `homeassistant.reload_config_entry` with entry ID
3. Restart Home Assistant
4. Try removal again

### Orphan Entities After Removal

1. Navigate to Developer Tools > States
2. Find orphan entities
3. Manually remove via entity registry

---

## Archival Recommendations

For long-term storage of test results:

```
test_archive/
├── YYYYMMDD_session_N/
│   ├── test_session_log.md
│   ├── bug_reports/
│   │   ├── BUG_001.md
│   │   └── BUG_002.md
│   ├── logs/
│   │   └── kospel_logs.txt
│   ├── screenshots/
│   │   └── *.png
│   └── state_files/
│       ├── initial_state.yaml
│       └── final_state.yaml
└── summary/
    └── test_results_summary.md
```
