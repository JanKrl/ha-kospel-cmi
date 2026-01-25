# Test Execution

## How to Run a Test

1. **Set Initial State**
   - Copy YAML from test scenario to `simulation_state.yaml`
   - Or copy a pre-made state from `initial_states/`

2. **Wait for Refresh**
   - HA refreshes every ~30 seconds
   - Or restart Home Assistant for immediate effect

3. **Perform Action**
   - If "HA → File": Change value in Home Assistant UI
   - If "File → HA": Edit `simulation_state.yaml` directly

4. **Verify**
   - Compare state file with expected YAML
   - Check HA UI shows expected values

5. **Record Result**
   - `[P]` = Pass
   - `[F]` = Fail

---

## Quick Result Tracker

```
Date: ___________
Tester: ___________

TC001 (Setup):    [ ] [ ] [ ] [ ] [ ]
TC002 (Climate):  [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]
TC003 (Sensors):  [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]
TC004 (Switches): [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]
TC005 (Simulator):[ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]

Failed: _________________________
Notes: _________________________
```

---

## Execution Order

1. **TC001** - Setup (must pass first)
2. **TC005.1-3** - Simulator basics
3. **TC003** - Sensors (read-only, easy)
4. **TC004** - Switches (bidirectional)
5. **TC002** - Climate (bidirectional)
6. **TC005.4+** - Remaining simulator tests

---

## Tips

- Keep `simulation_state.yaml` open in text editor
- Use refresh: Settings → System → Restart to force update
- Check `Developer Tools → States` for raw entity data
