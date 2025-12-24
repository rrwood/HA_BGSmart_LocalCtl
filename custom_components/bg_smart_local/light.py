"""Support for BG Smart Local Control lights."""
import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BG Smart lights from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    device = data["device"]
    
    _LOGGER.debug("Setting up BG Smart Local lights")
    
    # Get device parameters to discover devices
    try:
        # First get property count
        count = await device.get_property_count()
        _LOGGER.debug("Property count: %s", count)
        
        if count <= 0:
            _LOGGER.error("Property count is %s, cannot set up lights", count)
            return
        
        # Get all properties
        properties = await device.get_property_values()
        _LOGGER.debug("Properties: %s", properties)
        
        if not properties:
            _LOGGER.error("Failed to get properties from device")
            return
        
        # Get params
        params = await device.get_params()
        _LOGGER.info("Device params: %s", params)
        
        if not params:
            _LOGGER.error("No params found in device properties")
            return
        
        # Create a light entity for each device in params
        entities = []
        for device_name in params.keys():
            _LOGGER.info("Creating light entity for device: %s", device_name)
            entities.append(BGSmartDimmer(device, device_name, entry))
        
        if entities:
            _LOGGER.info("Adding %s light entities", len(entities))
            async_add_entities(entities, update_before_add=True)
        else:
            _LOGGER.warning("No devices found in parameters")
            
    except Exception as ex:
        _LOGGER.error("Failed to set up lights: %s", ex, exc_info=True)


class BGSmartDimmer(LightEntity):
    """Representation of a BG Smart Dimmer."""
    
    def __init__(self, device, device_name: str, entry: ConfigEntry) -> None:
        """Initialize the dimmer."""
        self._device = device
        self._device_name = device_name
        self._attr_unique_id = f"{entry.entry_id}_{device_name}"
        self._attr_name = f"BG Smart {device_name}"
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_is_on = False
        self._attr_brightness = None
        
        _LOGGER.debug("Initialized dimmer for %s", device_name)
    
    @property
    def brightness(self) -> int | None:
        """Return the brightness (0-255)."""
        if self._attr_brightness is None:
            return None
        # Convert from 0-100 to 0-255
        return int(self._attr_brightness * 2.55)
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        _LOGGER.debug("Turn on %s, brightness=%s", self._device_name, brightness)
        
        # Determine brightness value to send (0-100)
        if brightness is not None:
            brightness_pct = int(brightness / 2.55)
        else:
            brightness_pct = 100  # Default to full brightness
        
        # Set both Power and Brightness parameters
        success = await self._device.set_param(
            self._device_name,
            "Power",
            {"power": 1}
        )
        
        if success and brightness is not None:
            success = await self._device.set_param(
                self._device_name,
                "Brightness",
                {"brightness": brightness_pct}
            )
        
        if success:
            self._attr_is_on = True
            if brightness is not None:
                self._attr_brightness = brightness_pct
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to turn on %s", self._device_name)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        _LOGGER.debug("Turn off %s", self._device_name)
        
        success = await self._device.set_param(
            self._device_name,
            "Power",
            {"power": 0}
        )
        
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to turn off %s", self._device_name)
    
    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        try:
            _LOGGER.debug("Updating %s", self._device_name)
            
            params = await self._device.get_params()
            if self._device_name not in params:
                _LOGGER.warning("Device %s not found in params", self._device_name)
                return
                
            device_params = params[self._device_name]
            _LOGGER.debug("Device %s params: %s", self._device_name, device_params)
            
            # Check for Power parameter
            if "Power" in device_params:
                power_state = device_params["Power"].get("power", 0)
                self._attr_is_on = power_state == 1
                _LOGGER.debug("Power state: %s", power_state)
            
            # Check for Brightness parameter
            if "Brightness" in device_params:
                brightness = device_params["Brightness"].get("brightness", 0)
                self._attr_brightness = brightness
                _LOGGER.debug("Brightness: %s", brightness)
                    
        except Exception as ex:
            _LOGGER.error("Failed to update %s: %s", self._device_name, ex, exc_info=True)