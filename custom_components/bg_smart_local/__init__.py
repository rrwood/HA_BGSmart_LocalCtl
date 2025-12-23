"""The BG Smart Local Control integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the BG Smart Local Control component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BG Smart Local Control from a config entry."""
    from .esp_local_control import ESPLocalDevice
    
    host = entry.data["host"]
    port = entry.data.get("port", 80)
    node_id = entry.data.get("node_id", "")
    pop = entry.data.get("pop", "")
    security_type = entry.data.get("security_type", 0)
    
    device = ESPLocalDevice(host, port, node_id, pop, security_type)
    
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "host": host,
        "port": port
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok