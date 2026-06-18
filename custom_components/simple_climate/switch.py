"""Safety lockout switch for the Simple Climate integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.climate import HVACMode
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_COOL_SWITCH, CONF_HEAT_SWITCH, DOMAIN

if TYPE_CHECKING:
    from .climate import SimpleClimate

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the safety lockout switch for a config entry."""
    climate: SimpleClimate = hass.data[DOMAIN][entry.entry_id]
    lockout_switch = SafetyLockoutSwitch(hass, entry, climate)
    climate.lockout_switch = lockout_switch
    async_add_entities([lockout_switch])


class SafetyLockoutSwitch(SwitchEntity, RestoreEntity):
    """Manual-reset safety lockout switch for the climate controller."""

    _attr_should_poll = False

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, climate: SimpleClimate
    ) -> None:
        """Initialize the lockout switch linked to a climate entity."""
        self.hass = hass
        self.entry = entry
        self._climate = climate
        self._attr_unique_id = f"{entry.entry_id}_lockout"
        self._attr_name = f"{entry.data.get('name', 'Simple Climate')} Lockout"
        self._attr_is_on = False
        self._attr_icon = "mdi:lock-open-variant"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name", "Simple Climate"),
            manufacturer="Simple Climate",
            model="Simple Climate Thermostat",
        )

    @property
    def icon(self) -> str:
        """Return the icon based on lock state."""
        return "mdi:lock" if self._attr_is_on else "mdi:lock-open-variant"

    async def async_added_to_hass(self) -> None:
        """Restore the lockout state from previous HA session."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            self._attr_is_on = last_state.state == STATE_ON
            self._climate._safety_lockout = self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Engage lockout: stop all effectors and set HVAC to off."""
        self._attr_is_on = True
        self.async_write_ha_state()
        self._climate._safety_lockout = True
        self._climate._attr_hvac_mode = HVACMode.OFF
        await self._climate._async_set_effector(
            self._climate._get_config(CONF_HEAT_SWITCH), False
        )
        await self._climate._async_set_effector(
            self._climate._get_config(CONF_COOL_SWITCH), False
        )
        self._climate.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Release lockout and let the climate resume normal operation."""
        self._attr_is_on = False
        self.async_write_ha_state()
        self._climate._safety_lockout = False
        await self._climate._async_update_state()
