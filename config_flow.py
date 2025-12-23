# config_flow.py
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

class BGSmartLocalFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BG Smart Local Control."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Test connection
            from .esp_local_control import ESPLocalDevice
            device = ESPLocalDevice(
                user_input["host"],
                user_input.get("port", 80),
                user_input.get("node_id", ""),
                user_input.get("pop", ""),
                user_input.get("security_type", 0)
            )
            
            try:
                # Try to get property count to verify connection
                count = await device.get_property_count()
                if count > 0:
                    return self.async_create_entry(
                        title=f"BG Smart Dimmer ({user_input['host']})",
                        data=user_input
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"
        
        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Optional("port", default=80): int,
            vol.Optional("node_id", default=""): str,
            vol.Optional("pop", default=""): str,
            vol.Optional("security_type", default=0): vol.In([0, 1]),
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )


