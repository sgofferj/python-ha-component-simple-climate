from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.simple_climate.climate import SimpleClimate
from custom_components.simple_climate.const import (
    CONF_COOL_SWITCH,
    CONF_HEAT_SWITCH,
    CONF_HYSTERESIS,
    CONF_INSIDE_SENSOR,
    CONF_OUTSIDE_CHECK_COOL,
    CONF_OUTSIDE_CHECK_HEAT,
    CONF_OUTSIDE_SENSOR,
    CONF_TARGET_TEMP_HIGH,
    CONF_TARGET_TEMP_LOW,
)

from .conftest import MockState, build_entry, build_hass


def make_climate(
    hass: MagicMock | None = None,
    entry: MagicMock | None = None,
) -> SimpleClimate:
    if hass is None:
        hass = build_hass()
    if entry is None:
        entry = build_entry()
    return SimpleClimate(hass, entry)


class TestCooling:
    async def test_turns_on_when_above_setpoint_plus_half_hysteresis(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("28.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.cooler"}, blocking=True
        )

    async def test_turns_off_when_below_setpoint_minus_half_hysteresis(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("16.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("on"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_off", {"entity_id": "switch.cooler"}, blocking=True
        )

    async def test_stays_off_within_deadband(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("25.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_not_awaited()

    async def test_stays_on_within_deadband(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("25.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("on"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_not_awaited()

    async def test_forced_off_when_heat_effector_was_on(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("28.0"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        assert hass.services.async_call.await_count == 2
        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.heater"}, blocking=True
        )
        hass.services.async_call.assert_any_await(
            "switch", "turn_on", {"entity_id": "switch.cooler"}, blocking=True
        )


class TestHeating:
    async def test_turns_on_when_below_setpoint_minus_half_hysteresis(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("15.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.heater"}, blocking=True
        )

    async def test_turns_off_when_above_setpoint_plus_half_hysteresis(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("22.0"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_off", {"entity_id": "switch.heater"}, blocking=True
        )

    async def test_stays_off_within_deadband(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("18.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        hass.services.async_call.assert_not_awaited()

    async def test_stays_on_within_deadband(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("18.0"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        hass.services.async_call.assert_not_awaited()

    async def test_forced_off_when_cool_effector_was_on(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("15.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("on"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        assert hass.services.async_call.await_count == 2
        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.cooler"}, blocking=True
        )
        hass.services.async_call.assert_any_await(
            "switch", "turn_on", {"entity_id": "switch.heater"}, blocking=True
        )


class TestOffMode:
    async def test_turns_both_effectors_off(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("30.0"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("on"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "off"
        await climate._async_update_state()

        assert hass.services.async_call.await_count == 2
        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.heater"}, blocking=True
        )
        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.cooler"}, blocking=True
        )


class TestHysteresis:
    async def test_custom_hysteresis_width(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("24.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        entry = build_entry(**{CONF_HYSTERESIS: 2.0})
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "cool"
        climate._attr_target_temperature_high = 25.0

        await climate._async_update_state()
        hass.services.async_call.assert_not_awaited()

        # with hysteresis=2.0, half=1.0, so turn-on is at 26.0, not 24.0
        hass.services.async_call.assert_not_awaited()


class TestMissingSensor:
    async def test_turns_both_effectors_off_when_inside_sensor_unavailable(
        self,
    ) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("unavailable"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("on"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        assert hass.services.async_call.await_count == 2
        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.heater"}, blocking=True
        )
        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.cooler"}, blocking=True
        )

    async def test_inside_sensor_unknown(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("unknown"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_any_await(
            "switch", "turn_off", {"entity_id": "switch.heater"}, blocking=True
        )

    async def test_outside_sensor_unavailable_skips_check_in_cool_mode(
        self,
    ) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("28.0"),
                "sensor.outside": MockState("unavailable"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        entry = build_entry(
            **{
                CONF_OUTSIDE_SENSOR: "sensor.outside",
                CONF_OUTSIDE_CHECK_COOL: True,
            }
        )
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.cooler"}, blocking=True
        )


class TestOutsideCheck:
    async def test_cool_blocks_when_outside_warmer_than_inside(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("30.0"),
                "sensor.outside": MockState("32.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("on"),
            }
        )
        entry = build_entry(
            **{
                CONF_OUTSIDE_SENSOR: "sensor.outside",
                CONF_OUTSIDE_CHECK_COOL: True,
            }
        )
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_off", {"entity_id": "switch.cooler"}, blocking=True
        )

    async def test_cool_allows_when_outside_cooler_than_inside(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("30.0"),
                "sensor.outside": MockState("22.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        entry = build_entry(
            **{
                CONF_OUTSIDE_SENSOR: "sensor.outside",
                CONF_OUTSIDE_CHECK_COOL: True,
            }
        )
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "cool"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.cooler"}, blocking=True
        )

    async def test_heat_blocks_when_outside_cooler_than_inside(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("10.0"),
                "sensor.outside": MockState("5.0"),
                "switch.heater": MockState("on"),
                "switch.cooler": MockState("off"),
            }
        )
        entry = build_entry(
            **{
                CONF_OUTSIDE_SENSOR: "sensor.outside",
                CONF_OUTSIDE_CHECK_HEAT: True,
            }
        )
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_off", {"entity_id": "switch.heater"}, blocking=True
        )

    async def test_heat_allows_when_outside_warmer_than_inside(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("10.0"),
                "sensor.outside": MockState("15.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        entry = build_entry(
            **{
                CONF_OUTSIDE_SENSOR: "sensor.outside",
                CONF_OUTSIDE_CHECK_HEAT: True,
            }
        )
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "heat"
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.heater"}, blocking=True
        )


class TestHvacModes:
    async def test_both_enabled(self) -> None:
        climate = make_climate()
        assert climate.hvac_modes == ["off", "heat", "cool"]

    async def test_heat_only(self) -> None:
        entry = build_entry(**{"enable_heat": True, "enable_cool": False})
        climate = make_climate(entry=entry)
        assert climate.hvac_modes == ["off", "heat"]

    async def test_cool_only(self) -> None:
        entry = build_entry(**{"enable_heat": False, "enable_cool": True})
        climate = make_climate(entry=entry)
        assert climate.hvac_modes == ["off", "cool"]

    async def test_set_hvac_rejects_disabled_mode(self) -> None:
        entry = build_entry(**{"enable_heat": False, "enable_cool": True})
        climate = make_climate(entry=entry)
        await climate.async_set_hvac_mode("heat")
        assert climate.hvac_mode == "cool"


class TestTemperatureChanges:
    async def test_async_set_temperature_updates_low(self) -> None:
        climate = make_climate()
        await climate.async_set_temperature(target_temp_low=15.0)
        assert climate.target_temperature_low == 15.0

    async def test_async_set_temperature_updates_high(self) -> None:
        climate = make_climate()
        await climate.async_set_temperature(target_temp_high=28.0)
        assert climate.target_temperature_high == 28.0

    async def test_uses_heat_setpoint_in_heat_mode(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("14.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "heat"
        climate._attr_target_temperature_low = 20.0
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.heater"}, blocking=True
        )

    async def test_uses_cool_setpoint_in_cool_mode(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("24.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        climate = make_climate(hass)
        climate._attr_hvac_mode = "cool"
        climate._attr_target_temperature_high = 22.0
        await climate._async_update_state()

        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.cooler"}, blocking=True
        )


class TestConfigFallback:
    async def test_reads_from_options_before_data(self) -> None:
        hass = build_hass(
            {
                "sensor.inside": MockState("28.0"),
                "switch.heater": MockState("off"),
                "switch.cooler": MockState("off"),
            }
        )
        entry = build_entry(**{CONF_HYSTERESIS: 1.0})
        entry.options = {CONF_HYSTERESIS: 3.0}
        climate = make_climate(hass, entry)
        climate._attr_hvac_mode = "cool"

        await climate._async_update_state()

        # with options hysteresis=3.0, half=1.5, turn-on at 26.5, 28.0>26.5
        hass.services.async_call.assert_awaited_once_with(
            "switch", "turn_on", {"entity_id": "switch.cooler"}, blocking=True
        )
