"""Config and options flow for the Simple Climate integration."""

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
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

HVAC_OPTIONS = ["cool", "heat", "off"]


class SimpleClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Config flow for Simple Climate."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial config step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Simple Climate"): str,
                    vol.Required(CONF_INSIDE_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="temperature",
                        ),
                    ),
                    vol.Required(CONF_HEAT_SWITCH): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch"),
                    ),
                    vol.Required(CONF_COOL_SWITCH): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch"),
                    ),
                    vol.Required(
                        CONF_TARGET_TEMP_LOW, default=DEFAULT_TARGET_TEMP_LOW
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=50,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Required(
                        CONF_TARGET_TEMP_HIGH, default=DEFAULT_TARGET_TEMP_HIGH
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=50,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Required(
                        CONF_DEFAULT_MODE, default="cool"
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=HVAC_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Optional(CONF_OUTSIDE_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="temperature",
                        ),
                    ),
                    vol.Optional(
                        CONF_HYSTERESIS, default=DEFAULT_HYSTERESIS
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.1,
                            max=5.0,
                            step=0.1,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Required(
                        CONF_ENABLE_HEAT, default=DEFAULT_ENABLE_HEAT
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_ENABLE_COOL, default=DEFAULT_ENABLE_COOL
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_OUTSIDE_CHECK_HEAT, default=False
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_OUTSIDE_CHECK_COOL, default=False
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_SAFETY_SHUTDOWN_LOW, default=0
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=30,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_SAFETY_SHUTDOWN_HIGH, default=0
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=60,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return SimpleClimateOptionsFlow(config_entry)


class SimpleClimateOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Simple Climate."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize with the config entry."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle the options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INSIDE_SENSOR,
                        default=self.config_entry.data.get(CONF_INSIDE_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="temperature",
                        ),
                    ),
                    vol.Required(
                        CONF_HEAT_SWITCH,
                        default=self.config_entry.data.get(CONF_HEAT_SWITCH),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch"),
                    ),
                    vol.Required(
                        CONF_COOL_SWITCH,
                        default=self.config_entry.data.get(CONF_COOL_SWITCH),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch"),
                    ),
                    vol.Required(
                        CONF_TARGET_TEMP_LOW,
                        default=self.config_entry.data.get(
                            CONF_TARGET_TEMP_LOW, DEFAULT_TARGET_TEMP_LOW
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=50,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Required(
                        CONF_TARGET_TEMP_HIGH,
                        default=self.config_entry.data.get(
                            CONF_TARGET_TEMP_HIGH, DEFAULT_TARGET_TEMP_HIGH
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=50,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_OUTSIDE_SENSOR,
                        default=self.config_entry.data.get(CONF_OUTSIDE_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="temperature",
                        ),
                    ),
                    vol.Optional(
                        CONF_HYSTERESIS,
                        default=self.config_entry.data.get(
                            CONF_HYSTERESIS, DEFAULT_HYSTERESIS
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.1,
                            max=5.0,
                            step=0.1,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Required(
                        CONF_ENABLE_HEAT,
                        default=self.config_entry.data.get(
                            CONF_ENABLE_HEAT, DEFAULT_ENABLE_HEAT
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_ENABLE_COOL,
                        default=self.config_entry.data.get(
                            CONF_ENABLE_COOL, DEFAULT_ENABLE_COOL
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_OUTSIDE_CHECK_HEAT,
                        default=self.config_entry.data.get(
                            CONF_OUTSIDE_CHECK_HEAT, False
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_OUTSIDE_CHECK_COOL,
                        default=self.config_entry.data.get(
                            CONF_OUTSIDE_CHECK_COOL, False
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_SAFETY_SHUTDOWN_LOW,
                        default=self.config_entry.data.get(CONF_SAFETY_SHUTDOWN_LOW, 0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=30,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_SAFETY_SHUTDOWN_HIGH,
                        default=self.config_entry.data.get(
                            CONF_SAFETY_SHUTDOWN_HIGH, 0
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=60,
                            step=0.5,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                }
            ),
        )
