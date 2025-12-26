"""The BG Smart Local Control integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT]
SCAN_INTERVAL = timedelta(seconds=30)


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
    
    # Create coordinator for polling
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="bg_smart_local",
        update_method=device.get_params,
        update_interval=SCAN_INTERVAL,
    )
    
    # Initial refresh
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "coordinator": coordinator,
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