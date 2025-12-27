"""Config flow for BG Smart Local Control integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import network

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_NODE_ID = "node_id"
CONF_POP = "pop"
CONF_SECURITY_TYPE = "security_type"

# Force Sec1 security (encryption with PoP)
SECURITY_TYPE_SEC1 = 1
DEFAULT_PORT = 8080


class BGSmartLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BG Smart Local Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Force Sec1 security
            user_input[CONF_SECURITY_TYPE] = SECURITY_TYPE_SEC1
            
            # Test connection
            try:
                from .esp_local_control import ESPLocalDevice
                
                device = ESPLocalDevice(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input.get(CONF_NODE_ID, ""),
                    user_input[CONF_POP],
                    SECURITY_TYPE_SEC1
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

        # Get Home Assistant's local IP to suggest device IP
        ha_ip = await self._get_ha_local_ip()
        suggested_ip = self._suggest_device_ip(ha_ip)
        
        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default=suggested_ip): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_POP, description="Proof of Possession (PoP) key"): str,
            vol.Optional(CONF_NODE_ID, default=""): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "pop_help": "The PoP key is usually printed on the device label or found in the BG Smart app settings."
            }
        )
    
    async def _get_ha_local_ip(self) -> str:
        """Get Home Assistant's local IP address."""
        try:
            # Get the adapter with default route
            adapters = await network.async_get_adapters(self.hass)
            for adapter in adapters:
                if adapter.get("default") and adapter.get("ipv4"):
                    for ipv4 in adapter["ipv4"]:
                        if ipv4.get("address"):
                            return ipv4["address"]
        except Exception as ex:
            _LOGGER.debug("Could not determine HA IP: %s", ex)
        
        return "192.168.1.1"
    
    def _suggest_device_ip(self, ha_ip: str) -> str:
        """Suggest device IP based on HA IP (replace last octet with xxx)."""
        try:
            parts = ha_ip.split(".")
            if len(parts) == 4:
                # Replace last octet with xxx
                return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
        except Exception:
            pass
        
        return "192.168.1.xxx"