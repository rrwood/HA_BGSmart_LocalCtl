
# __init__.py
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bg_smart_local"
PLATFORMS = ["light"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the BG Smart Local component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up BG Smart Local from a config entry."""
    from .esp_local_control import ESPLocalDevice
    
    host = entry.data["host"]
    port = entry.data.get("port", 80)
    node_id = entry.data.get("node_id", "")
    pop = entry.data.get("pop", "")
    security_type = entry.data.get("security_type", 0)  # 0 = sec0, 1 = sec1
    
    device = ESPLocalDevice(host, port, node_id, pop, security_type)
    
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "host": host,
        "port": port
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


