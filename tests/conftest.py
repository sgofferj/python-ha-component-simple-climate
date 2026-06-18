from __future__ import annotations

import sys
from enum import Enum
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub classes used as base / enum / feature-flag by our component code
# ---------------------------------------------------------------------------


class HVACMode(str, Enum):
    HEAT = "heat"
    COOL = "cool"
    OFF = "off"


class ClimateEntityFeature:
    TARGET_TEMPERATURE = 1
    TARGET_TEMPERATURE_RANGE = 2
    TURN_OFF = 128
    TURN_ON = 256


class ClimateEntity:
    _attr_precision = None
    _attr_target_temperature_step = None
    _attr_supported_features = None
    _attr_unique_id = None
    _attr_name = None
    _attr_hvac_mode = None
    _attr_target_temperature_low = None
    _attr_target_temperature_high = None
    _attr_temperature_unit = None

    @property
    def target_temperature_low(self):
        return self._attr_target_temperature_low

    @property
    def target_temperature_high(self):
        return self._attr_target_temperature_high

    async def async_added_to_hass(self):
        pass

    def async_write_ha_state(self):
        pass

    async def async_get_last_state(self):
        return None


class SwitchEntity:
    _attr_should_poll = None
    _attr_is_on = None
    _attr_unique_id = None
    _attr_name = None

    async def async_turn_on(self, **kwargs):
        pass

    async def async_turn_off(self, **kwargs):
        pass

    def async_write_ha_state(self):
        pass


class RestoreEntity:
    async def async_added_to_hass(self):
        pass

    async def async_get_last_state(self):
        return None


# ---------------------------------------------------------------------------
#  Inject mocks for all ``homeassistant`` sub-modules into sys.modules so
#  the component files can be imported without the real HA package.
# ---------------------------------------------------------------------------


def _build_module_tree() -> dict[str, Any]:
    const = MagicMock()
    const.ATTR_ENTITY_ID = "entity_id"
    const.ATTR_TARGET_TEMP_HIGH = "target_temp_high"
    const.ATTR_TARGET_TEMP_LOW = "target_temp_low"
    const.ATTR_TEMPERATURE = "temperature"
    const.SERVICE_TURN_OFF = "turn_off"
    const.SERVICE_TURN_ON = "turn_on"
    const.STATE_ON = "on"
    const.STATE_UNAVAILABLE = "unavailable"
    const.STATE_UNKNOWN = "unknown"
    const.UnitOfTemperature = MagicMock()
    const.UnitOfTemperature.CELSIUS = "°C"
    const.UnitOfTemperature.FAHRENHEIT = "°F"

    climate_mod = MagicMock()
    climate_mod.ClimateEntity = ClimateEntity
    climate_mod.ClimateEntityFeature = ClimateEntityFeature
    climate_mod.HVACMode = HVACMode
    climate_mod.ATTR_TARGET_TEMP_HIGH = "target_temp_high"
    climate_mod.ATTR_TARGET_TEMP_LOW = "target_temp_low"

    switch_mod = MagicMock()
    switch_mod.SwitchEntity = SwitchEntity

    restore_state_mod = MagicMock()
    restore_state_mod.RestoreEntity = RestoreEntity

    device_registry_mod = MagicMock()
    device_registry_mod.DeviceInfo = MagicMock

    event = MagicMock()
    event.async_track_state_change_event = MagicMock(return_value=MagicMock())
    event.async_track_time_interval = MagicMock(return_value=MagicMock())

    return {
        "homeassistant": MagicMock(),
        "homeassistant.components": MagicMock(),
        "homeassistant.components.climate": climate_mod,
        "homeassistant.components.switch": switch_mod,
        "homeassistant.config_entries": MagicMock(),
        "homeassistant.const": const,
        "homeassistant.core": MagicMock(callback=lambda x: x),
        "homeassistant.helpers": MagicMock(),
        "homeassistant.helpers.device_registry": device_registry_mod,
        "homeassistant.helpers.entity_platform": MagicMock(),
        "homeassistant.helpers.event": event,
        "homeassistant.helpers.restore_state": restore_state_mod,
    }


for _mod_name, _mod in _build_module_tree().items():
    sys.modules[_mod_name] = _mod


# ---------------------------------------------------------------------------
#  Test helpers
# ---------------------------------------------------------------------------


class MockState:
    def __init__(self, state: str, **attributes: Any) -> None:
        self.state = state
        self.attributes = attributes


def build_hass(states: dict[str, MockState] | None = None) -> MagicMock:
    hass = MagicMock()
    hass.states.get = MagicMock(side_effect=lambda eid: (states or {}).get(eid))
    hass.services.async_call = AsyncMock()
    return hass


def build_entry(**overrides: Any) -> MagicMock:
    data: dict[str, Any] = {
        "name": "Test Climate",
        "inside_sensor": "sensor.inside",
        "heat_switch": "switch.heater",
        "cool_switch": "switch.cooler",
        "target_temperature_low": 18.0,
        "target_temperature_high": 25.0,
        "hysteresis": 0.5,
        "outside_check_heat": False,
        "outside_check_cool": False,
        "enable_heat": True,
        "enable_cool": True,
        "default_mode": "cool",
    }
    data.update(overrides)
    entry = MagicMock()
    entry.entry_id = "test_id"
    entry.data = data
    entry.options = {}
    return entry


@pytest.fixture
def hass() -> MagicMock:
    return build_hass()


@pytest.fixture
def entry() -> MagicMock:
    return build_entry()
