# Environment Setup

## Quick Setup

### 1. Set Environment Variable

**Docker:**
```yaml
environment:
  - SIMULATION_MODE=1
```

**Shell:**
```bash
export SIMULATION_MODE=1
```

### 2. Copy Integration Files

```bash
cp -r custom_components/kospel <HA_CONFIG>/custom_components/
```

### 3. Copy Initial State

```bash
mkdir -p <HA_CONFIG>/custom_components/kospel/data
cp docs/test_campaign/initial_states/state_baseline.yaml \
   <HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
```

### 4. Restart Home Assistant

### 5. Add Integration

Settings → Devices & Services → Add Integration → "Kospel Electric Heaters"

---

## File Locations

| File | Location |
|------|----------|
| Integration | `<HA_CONFIG>/custom_components/kospel/` |
| State File | `<HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml` |
| Initial States | `docs/test_campaign/initial_states/` |

---

## Checklist

- [ ] `SIMULATION_MODE=1` set
- [ ] Integration files copied
- [ ] Home Assistant restarted
- [ ] Integration added
- [ ] 14 entities visible

---

## Debug Logging (Optional)

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.kospel: debug
```
