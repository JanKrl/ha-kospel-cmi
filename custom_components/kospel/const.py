"""Constants for the Kospel integration."""

from datetime import timedelta

DOMAIN = "kospel"

# Configuration keys
CONF_HEATER_IP = "heater_ip"
CONF_DEVICE_ID = "device_id"
CONF_SIMULATION_MODE = "simulation_mode"

# Update intervals
SCAN_INTERVAL = timedelta(seconds=30)

# Simulation mode constants
SIMULATION_MODE_ENV_VAR = "SIMULATION_MODE"
