"""Constants for the Simple Climate integration."""

DOMAIN = "simple_climate"

CONF_INSIDE_SENSOR = "inside_sensor"
CONF_OUTSIDE_SENSOR = "outside_sensor"
CONF_HEAT_SWITCH = "heat_switch"
CONF_COOL_SWITCH = "cool_switch"
CONF_TARGET_TEMP_LOW = "target_temperature_low"
CONF_TARGET_TEMP_HIGH = "target_temperature_high"
CONF_HYSTERESIS = "hysteresis"
CONF_OUTSIDE_CHECK_HEAT = "outside_check_heat"
CONF_OUTSIDE_CHECK_COOL = "outside_check_cool"
CONF_ENABLE_HEAT = "enable_heat"
CONF_ENABLE_COOL = "enable_cool"
CONF_SAFETY_SHUTDOWN_LOW = "safety_shutdown_low"
CONF_SAFETY_SHUTDOWN_HIGH = "safety_shutdown_high"
CONF_DEFAULT_MODE = "default_mode"

DEFAULT_HYSTERESIS = 0.5
DEFAULT_TARGET_TEMP_LOW = 18.0
DEFAULT_TARGET_TEMP_HIGH = 25.0
DEFAULT_ENABLE_HEAT = True
DEFAULT_ENABLE_COOL = True

ATTR_INSIDE_TEMP = "inside_temperature"
ATTR_OUTSIDE_TEMP = "outside_temperature"
ATTR_HEAT_SWITCH = "heat_switch"
ATTR_COOL_SWITCH = "cool_switch"
ATTR_SAFETY_LOCKOUT = "safety_lockout"
