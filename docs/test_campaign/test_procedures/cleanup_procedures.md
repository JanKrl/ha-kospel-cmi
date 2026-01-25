# Cleanup Procedures

## Reset State File

**Option A - Delete and recreate:**
```bash
rm <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
# Integration will create fresh file on next refresh
```

**Option B - Replace with baseline:**
```bash
cp docs/test_campaign/initial_states/state_baseline.yaml \
   <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
```

---

## Reset Integration

1. Settings → Devices & Services
2. Click Kospel integration
3. Click ⋮ menu → Delete
4. Confirm deletion
5. Re-add integration

---

## Full Reset

```bash
# Remove integration via HA UI first, then:
rm -rf <HA_CONFIG>/custom_components/kospel
# Re-copy integration files
cp -r custom_components/kospel <HA_CONFIG>/custom_components/
# Restart HA
```

---

## Initial State Files

Use these to reset to known states:

| File | Description |
|------|-------------|
| `state_baseline.yaml` | Winter mode, standard temps |
| `state_off.yaml` | Heater OFF |
| `state_summer.yaml` | Summer mode |
| `state_winter_all_features.yaml` | Winter + Manual + Water |
| `state_all_running.yaml` | All pumps, CO valve |
| `state_minimal.yaml` | Only essential registers |
