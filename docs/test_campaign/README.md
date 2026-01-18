# Manual Test Campaign - Kospel Home Assistant Integration

## Campaign Overview

**Version:** 1.0  
**Date:** January 2026  
**Project Phase:** Early Development (Layer 4 - Integration Layer)  
**Test Mode:** Simulation Only (No Physical Hardware)

## Campaign Goals

### Primary Objectives

1. **Validate Integration Functionality**
   - Verify the integration loads correctly in Home Assistant
   - Confirm all entities are created and visible in the UI
   - Test basic read/write operations through Home Assistant controls

2. **Identify Early Bugs**
   - Discover functional defects before hardware testing
   - Identify usability issues in the Home Assistant UI
   - Find edge cases in state management and data flow

3. **Inform Development Roadmap**
   - Document areas requiring improvement
   - Prioritize bug fixes and enhancements for upcoming sprints
   - Identify missing features or incomplete implementations

### Success Criteria

- [ ] All entities appear correctly in Home Assistant UI
- [ ] All sensor values display correctly from simulator state
- [ ] All control operations (switches, climate controls) work as expected
- [ ] State changes persist across coordinator updates
- [ ] Error handling works appropriately for edge cases
- [ ] Integration survives Home Assistant restart

## Test Scope

### In Scope

| Component | Description | Test Type |
|-----------|-------------|-----------|
| Climate Entity | Main heater control (HVAC mode, preset, temperature) | Functional |
| Temperature Sensors | 7 temperature readings | Functional |
| Pressure Sensor | System pressure reading | Functional |
| Status Sensors | Pump status, valve position | Functional |
| Switch Entities | Manual mode, water heater toggles | Functional |
| Integration Setup | Config flow, entity creation | Installation |
| Simulator | State persistence, read/write | System |

### Out of Scope

- Physical heater hardware testing (future phase)
- Performance/load testing
- Security testing
- Multi-instance testing
- Automated regression testing (unit tests currently broken)

## Test Environment

### Required Setup

1. **Home Assistant Instance**
   - Version: 2024.1 or later
   - Installation type: Any (OS, Container, Core, Supervised)
   
2. **Environment Variables**
   ```bash
   SIMULATION_MODE=1
   ```

3. **Integration Installation**
   - Follow steps in `INSTALLATION.md`
   - Verify directory structure is complete

### Simulator State File

Location: `<config>/custom_components/kospel/data/simulation_state.yaml`

This file can be manually edited to set up test scenarios.

## Test Documentation Structure

```
docs/test_campaign/
├── README.md                    # This file - overview and goals
├── test_scenarios/
│   ├── TC001_integration_setup.md
│   ├── TC002_climate_entity.md
│   ├── TC003_sensor_entities.md
│   ├── TC004_switch_entities.md
│   └── TC005_simulator.md
├── test_procedures/
│   ├── environment_setup.md
│   ├── execution_checklist.md
│   └── cleanup_procedures.md
├── templates/
│   ├── bug_report_template.md
│   ├── test_result_template.md
│   └── test_session_log.md
└── results/
    └── .gitkeep                 # Results stored here per session
```

## Test Categories

### 1. Installation & Setup Tests (TC001)
- Integration discovery in Home Assistant
- Config flow completion
- Entity creation verification
- Restart resilience

### 2. Climate Entity Tests (TC002)
- HVAC mode changes (OFF, HEAT)
- Preset mode changes (winter, summer, off)
- Temperature adjustments
- State synchronization

### 3. Sensor Entity Tests (TC003)
- Temperature sensor readings
- Pressure sensor reading
- Pump status display
- Valve position display
- Unit of measurement verification

### 4. Switch Entity Tests (TC004)
- Manual mode toggle
- Water heater toggle
- State persistence after toggle
- UI feedback

### 5. Simulator Tests (TC005)
- State file creation
- State persistence across restarts
- Register read/write operations
- Manual state file editing

## Bug Severity Levels

| Level | Description | Example |
|-------|-------------|---------|
| **Critical** | Integration fails to load or crashes | Import errors, missing dependencies |
| **High** | Major feature completely broken | Cannot change heater mode |
| **Medium** | Feature partially working or incorrect values | Wrong temperature displayed |
| **Low** | Minor issues, cosmetic problems | Entity naming issues |

## Sprint Planning Integration

Test results will be categorized for sprint planning:

### P1 - Must Fix This Sprint
- Critical bugs blocking core functionality
- Issues preventing simulation testing

### P2 - Should Fix This Sprint
- High severity bugs affecting user experience
- Missing error handling for common scenarios

### P3 - Backlog
- Low severity issues
- Enhancement requests
- Nice-to-have improvements

## Test Execution Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Setup | 1-2 hours | Environment setup, integration installation |
| Execution | 4-6 hours | Execute all test scenarios |
| Reporting | 1-2 hours | Document results, create bug reports |
| Analysis | 1 hour | Prioritize issues for sprint planning |

## Reference Documents

- [Architecture Diagram](../architecture.mermaid)
- [Technical Specifications](../technical.md)
- [Project Status](../status.md)
- [Installation Guide](../../INSTALLATION.md)
- [README](../../README.md)

## Contact

For questions about this test campaign, refer to the project repository documentation or contact the development team.
