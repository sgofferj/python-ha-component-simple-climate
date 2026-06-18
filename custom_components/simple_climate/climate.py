"""Climate entity for the Simple Climate integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.climate import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_COOL_SWITCH,
    ATTR_HEAT_SWITCH,
    ATTR_INSIDE_TEMP,
    ATTR_OUTSIDE_TEMP,
    CONF_COOL_SWITCH,
    CONF_DEFAULT_MODE,
    CONF_ENABLE_COOL,
    CONF_ENABLE_HEAT,
    CONF_HEAT_SWITCH,
    CONF_HYSTERESIS,
    CONF_INSIDE_SENSOR,
    CONF_OUTSIDE_CHECK_COOL,
    CONF_OUTSIDE_CHECK_HEAT,
    CONF_OUTSIDE_SENSOR,
    CONF_SAFETY_SHUTDOWN_HIGH,
    CONF_SAFETY_SHUTDOWN_LOW,
    CONF_TARGET_TEMP_HIGH,
    CONF_TARGET_TEMP_LOW,
    DEFAULT_ENABLE_COOL,
    DEFAULT_ENABLE_HEAT,
    DEFAULT_HYSTERESIS,
    DEFAULT_TARGET_TEMP_HIGH,
    DEFAULT_TARGET_TEMP_LOW,
    DOMAIN,
)

if TYPE_CHECKING:
    from .switch import SafetyLockoutSwitch

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Simple Climate entity from a config entry."""
    climate = SimpleClimate(hass, entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = climate
    async_add_entities([climate])


class SimpleClimate(ClimateEntity, RestoreEntity):
    """Dual-effector heat/cool climate control entity."""

    _attr_precision = 0.1
    _attr_target_temperature_step = 0.1
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the climate entity from config entry data."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data.get("name", "Simple Climate")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=self._attr_name,
            manufacturer="Simple Climate",
            model="Simple Climate Thermostat",
        )
        self._attr_target_temperature_low = entry.data.get(
            CONF_TARGET_TEMP_LOW, DEFAULT_TARGET_TEMP_LOW
        )
        self._attr_target_temperature_high = entry.data.get(
            CONF_TARGET_TEMP_HIGH, DEFAULT_TARGET_TEMP_HIGH
        )

        default_mode = entry.data.get(CONF_DEFAULT_MODE, HVACMode.COOL)
        self._attr_hvac_mode = (
            default_mode
            if default_mode in (HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF)
            else HVACMode.OFF
        )

        self._current_temperature: float | None = None
        self._outside_temperature: float | None = None
        self._safety_lockout: bool = False
        self._unsub_listeners: list = []
        self.lockout_switch: SafetyLockoutSwitch | None = None

        self._detect_temperature_unit()

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return available HVAC modes based on config."""
        modes = [HVACMode.OFF]
        if self._get_config(CONF_ENABLE_HEAT, DEFAULT_ENABLE_HEAT):
            modes.append(HVACMode.HEAT)
        if self._get_config(CONF_ENABLE_COOL, DEFAULT_ENABLE_COOL):
            modes.append(HVACMode.COOL)
        return modes

    def _detect_temperature_unit(self) -> None:
        """Detect temperature unit from the inside sensor."""
        sensor_id = self.entry.data.get(CONF_INSIDE_SENSOR, "")
        state = self.hass.states.get(sensor_id)
        if (
            state
            and state.attributes.get("unit_of_measurement")
            == UnitOfTemperature.FAHRENHEIT
        ):
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        else:
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the current indoor temperature."""
        return self._current_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return self._attr_hvac_mode

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes for debugging."""
        return {
            ATTR_INSIDE_TEMP: self._current_temperature,
            ATTR_OUTSIDE_TEMP: self._outside_temperature,
            ATTR_HEAT_SWITCH: self._get_switch_state(
                self._get_config(CONF_HEAT_SWITCH)
            ),
            ATTR_COOL_SWITCH: self._get_switch_state(
                self._get_config(CONF_COOL_SWITCH)
            ),
        }

    def _get_config(self, key: str, default=None):
        """Read a config value from options (preferred) or data."""
        if key in self.entry.options:
            return self.entry.options[key]
        return self.entry.data.get(key, default)

    def _get_sensor_temp(self, entity_id: str) -> float | None:
        """Read and parse a temperature from the given sensor entity."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
            "none",
            "",
        ):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _get_switch_state(self, entity_id: str) -> bool | None:
        """Return the current on/off state of a switch entity."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        return state.state == STATE_ON

    def _is_effector_on(self, entity_id: str) -> bool:
        """Check whether a switch effector is currently on."""
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        return state.state == STATE_ON

    async def _async_set_effector(self, entity_id: str, turn_on: bool) -> None:
        """Turn a switch effector on or off, skipping if already in the desired state."""
        if not entity_id:
            return

        if self._is_effector_on(entity_id) == turn_on:
            return

        service = SERVICE_TURN_ON if turn_on else SERVICE_TURN_OFF
        await self.hass.services.async_call(
            "switch",
            service,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    async def _async_trigger_lockout(self, message: str) -> None:
        """Enter safety lockout: stop all effectors and create a notification."""
        self._safety_lockout = True
        self._attr_hvac_mode = HVACMode.OFF
        heat_switch = self._get_config(CONF_HEAT_SWITCH)
        cool_switch = self._get_config(CONF_COOL_SWITCH)
        await self._async_set_effector(heat_switch, False)
        await self._async_set_effector(cool_switch, False)

        if self.lockout_switch:
            await self.lockout_switch.async_turn_on()

        self.hass.async_create_task(
            self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Simple Climate Safety Shutdown",
                    "message": message,
                    "notification_id": (f"simple_climate_safety_{self.entry.entry_id}"),
                },
                blocking=True,
            )
        )
        _LOGGER.warning("Safety lockout triggered: %s", message)
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Read sensors and decide which effectors should be on or off."""
        inside_sensor = self._get_config(CONF_INSIDE_SENSOR)
        self._current_temperature = self._get_sensor_temp(inside_sensor)

        outside_sensor = self._get_config(CONF_OUTSIDE_SENSOR)
        self._outside_temperature = self._get_sensor_temp(outside_sensor)

        heat_switch = self._get_config(CONF_HEAT_SWITCH)
        cool_switch = self._get_config(CONF_COOL_SWITCH)

        if self._current_temperature is None:
            await self._async_set_effector(heat_switch, False)
            await self._async_set_effector(cool_switch, False)
            self.async_write_ha_state()
            return

        if self._safety_lockout:
            await self._async_set_effector(heat_switch, False)
            await self._async_set_effector(cool_switch, False)
            self.async_write_ha_state()
            return

        safety_high = self._get_config(CONF_SAFETY_SHUTDOWN_HIGH, 0)
        if safety_high and self._current_temperature > safety_high:
            await self._async_trigger_lockout(
                f"Heat safety shutdown: inside temp "
                f"{self._current_temperature:.1f}°C exceeded "
                f"{safety_high:.1f}°C."
            )
            return

        safety_low = self._get_config(CONF_SAFETY_SHUTDOWN_LOW, 0)
        if safety_low and self._current_temperature < safety_low:
            await self._async_trigger_lockout(
                f"Cool safety shutdown: inside temp "
                f"{self._current_temperature:.1f}°C dropped below "
                f"{safety_low:.1f}°C."
            )
            return

        hysteresis = self._get_config(CONF_HYSTERESIS, DEFAULT_HYSTERESIS)
        half_hyst = hysteresis / 2
        hvac = self._attr_hvac_mode

        if hvac == HVACMode.OFF:
            await self._async_set_effector(heat_switch, False)
            await self._async_set_effector(cool_switch, False)
            self.async_write_ha_state()
            return

        if hvac == HVACMode.COOL:
            if heat_switch != cool_switch:
                await self._async_set_effector(heat_switch, False)

            setpoint = (
                self.target_temperature_high or self._attr_target_temperature_high
            )
            cooler_on = self._is_effector_on(cool_switch)
            outside_check = self._get_config(CONF_OUTSIDE_CHECK_COOL, False)
            can_run = True
            if outside_check and self._outside_temperature is not None:
                if cooler_on:
                    can_run = (
                        self._outside_temperature
                        < self._current_temperature + half_hyst
                    )
                else:
                    can_run = (
                        self._outside_temperature
                        < self._current_temperature - half_hyst
                    )

            if not can_run:
                await self._async_set_effector(cool_switch, False)
            elif self._current_temperature > setpoint + half_hyst:
                await self._async_set_effector(cool_switch, True)
            elif self._current_temperature < setpoint - half_hyst:
                await self._async_set_effector(cool_switch, False)

        elif hvac == HVACMode.HEAT:
            if heat_switch != cool_switch:
                await self._async_set_effector(cool_switch, False)

            setpoint = self.target_temperature_low or self._attr_target_temperature_low
            heater_on = self._is_effector_on(heat_switch)
            outside_check = self._get_config(CONF_OUTSIDE_CHECK_HEAT, False)
            can_run = True
            if outside_check and self._outside_temperature is not None:
                if heater_on:
                    can_run = (
                        self._outside_temperature
                        > self._current_temperature - half_hyst
                    )
                else:
                    can_run = (
                        self._outside_temperature
                        > self._current_temperature + half_hyst
                    )

            if not can_run:
                await self._async_set_effector(heat_switch, False)
            elif self._current_temperature < setpoint - half_hyst:
                await self._async_set_effector(heat_switch, True)
            elif self._current_temperature > setpoint + half_hyst:
                await self._async_set_effector(heat_switch, False)

        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the climate entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_turn_on(self) -> None:
        """Turn the climate entity on to the first available mode."""
        if HVACMode.COOL in self.hvac_modes:
            await self.async_set_hvac_mode(HVACMode.COOL)
        elif HVACMode.HEAT in self.hvac_modes:
            await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode and clear lockout if needed."""
        if hvac_mode not in self.hvac_modes:
            return

        if self._safety_lockout:
            self._safety_lockout = False
            _LOGGER.info("Safety lockout cleared by user mode change")
            if self.lockout_switch:
                await self.lockout_switch.async_turn_off()
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {
                        "notification_id": (
                            f"simple_climate_safety_{self.entry.entry_id}"
                        )
                    },
                )
            )

        self._attr_hvac_mode = hvac_mode
        await self._async_update_state()

    async def async_set_temperature(self, **kwargs) -> None:
        """Update target temperature low/high setpoints."""
        if ATTR_TARGET_TEMP_LOW in kwargs:
            self._attr_target_temperature_low = kwargs[ATTR_TARGET_TEMP_LOW]
        if ATTR_TARGET_TEMP_HIGH in kwargs:
            self._attr_target_temperature_high = kwargs[ATTR_TARGET_TEMP_HIGH]
        await self._async_update_state()

    async def async_added_to_hass(self) -> None:
        """Restore prior state and start tracking sensors."""
        await super().async_added_to_hass()

        if last_state := await self.async_get_last_state():
            if ATTR_TARGET_TEMP_LOW in last_state.attributes:
                try:
                    self._attr_target_temperature_low = float(
                        last_state.attributes[ATTR_TARGET_TEMP_LOW]
                    )
                except (ValueError, TypeError):
                    pass
            if ATTR_TARGET_TEMP_HIGH in last_state.attributes:
                try:
                    self._attr_target_temperature_high = float(
                        last_state.attributes[ATTR_TARGET_TEMP_HIGH]
                    )
                except (ValueError, TypeError):
                    pass
            if last_state.state in [m.value for m in self.hvac_modes]:
                self._attr_hvac_mode = HVACMode(last_state.state)
            elif HVACMode.OFF in self.hvac_modes:
                self._attr_hvac_mode = HVACMode.OFF

        sensors_to_track = [
            self._get_config(CONF_INSIDE_SENSOR),
            self._get_config(CONF_OUTSIDE_SENSOR),
            self._get_config(CONF_HEAT_SWITCH),
            self._get_config(CONF_COOL_SWITCH),
        ]
        sensors_to_track = list(set(s for s in sensors_to_track if s))

        self._unsub_listeners.append(
            async_track_state_change_event(
                self.hass,
                sensors_to_track,
                self._async_state_changed_listener,
            )
        )

        self._unsub_listeners.append(
            async_track_time_interval(
                self.hass,
                self._async_periodic_update,
                UPDATE_INTERVAL,
            )
        )

        await self._async_update_state()

    @callback
    async def _async_state_changed_listener(self, _event) -> None:
        await self._async_update_state()

    @callback
    async def _async_periodic_update(self, _now) -> None:
        await self._async_update_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up event listeners on removal."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()
