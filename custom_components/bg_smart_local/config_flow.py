"""Config flow for BG Smart Local Control integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT

# Import DOMAIN from const
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_NODE_ID = "node_id"
CONF_POP = "pop"
CONF_SECURITY_TYPE = "security_type"


class BGSmartLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BG Smart Local Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Test connection
            try:
                from .esp_local_control import ESPLocalDevice
                
                device = ESPLocalDevice(
                    user_input[CONF_HOST],
                    user_input.get(CONF_PORT, 80),
                    user_input.get(CONF_NODE_ID, ""),
                    user_input.get(CONF_POP, ""),
                    user_input.get(CONF_SECURITY_TYPE, 0)
                )
                
                # Try to get property count to verify connection
                count = await device.get_property_count()
                if count > 0:
                    # Create unique ID based on host
                    await self.async_set_unique_id(user_input[CONF_HOST])
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"BG Smart ({user_input[CONF_HOST]})",
                        data=user_input
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.error("Failed to connect to device: %s", ex)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=80): int,
            vol.Optional(CONF_NODE_ID, default=""): str,
            vol.Optional(CONF_POP, default=""): str,
            vol.Optional(CONF_SECURITY_TYPE, default=0): vol.In([0, 1]),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )