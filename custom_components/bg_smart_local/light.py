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
    
    try:
        # Get device parameters
        params = await device.get_params()
        _LOGGER.info("Device params: %s", params)
        
        if not params:
            _LOGGER.error("No params found in device properties")
            return
        
        # Filter to only create entities for actual dimmer devices
        # Look for devices that have both "Power" and "brightness" parameters
        entities = []
        for device_name, device_params in params.items():
            if isinstance(device_params, dict) and "Power" in device_params and "brightness" in device_params:
                _LOGGER.info("Creating light entity for dimmer: %s", device_name)
                entities.append(BGSmartDimmer(device, device_name, device_params, entry))
            else:
                _LOGGER.debug("Skipping non-dimmer device: %s", device_name)
        
        if entities:
            _LOGGER.info("Adding %s light entities", len(entities))
            async_add_entities(entities, update_before_add=True)
        else:
            _LOGGER.warning("No dimmer devices found in parameters")
            
    except Exception as ex:
        _LOGGER.error("Failed to set up lights: %s", ex, exc_info=True)


class BGSmartDimmer(LightEntity):
    """Representation of a BG Smart Dimmer."""
    
    def __init__(self, device, device_name: str, device_params: dict, entry: ConfigEntry) -> None:
        """Initialize the dimmer."""
        self._device = device
        self._device_name = device_name
        
        # Use the "Name" parameter if available, otherwise use device_name
        friendly_name = device_params.get("Name", device_name)
        
        self._attr_unique_id = f"{entry.entry_id}_{device_name}"
        self._attr_name = friendly_name
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_is_on = False
        self._attr_brightness = None
        
        _LOGGER.info("Initialized dimmer: %s (device: %s)", friendly_name, device_name)
    
    @property
    def brightness(self) -> int | None:
        """Return the brightness (0-255)."""
        if self._attr_brightness is None:
            return None
        # Convert from 1-100 to 0-255
        # Device uses 1-100 range, HA uses 0-255
        return int((self._attr_brightness / 100) * 255)
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        _LOGGER.debug("Turn on %s, brightness=%s", self._device_name, brightness)
        
        try:
            # First, turn on the power if it's off
            success = await self._device.set_param(
                self._device_name,
                "Power",
                True  # Power is a boolean, not a dict
            )
            
            if not success:
                _LOGGER.error("Failed to turn on power for %s", self._device_name)
                return
            
            # Set brightness if specified
            if brightness is not None:
                # Convert from 0-255 to 1-100 (device range)
                brightness_pct = max(1, int((brightness / 255) * 100))
                
                success = await self._device.set_param(
                    self._device_name,
                    "brightness",  # lowercase 'brightness'
                    brightness_pct  # Direct integer, not a dict
                )
                
                if not success:
                    _LOGGER.error("Failed to set brightness for %s", self._device_name)
                    return
                
                self._attr_brightness = brightness_pct
            else:
                # If no brightness specified, set to 100%
                success = await self._device.set_param(
                    self._device_name,
                    "brightness",
                    100
                )
                self._attr_brightness = 100
            
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.info("Successfully turned on %s at brightness %s%%", 
                        self._device_name, self._attr_brightness)
            
        except Exception as ex:
            _LOGGER.error("Error turning on %s: %s", self._device_name, ex, exc_info=True)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        _LOGGER.debug("Turn off %s", self._device_name)
        
        try:
            success = await self._device.set_param(
                self._device_name,
                "Power",
                False  # Boolean value
            )
            
            if success:
                self._attr_is_on = False
                self.async_write_ha_state()
                _LOGGER.info("Successfully turned off %s", self._device_name)
            else:
                _LOGGER.error("Failed to turn off %s", self._device_name)
                
        except Exception as ex:
            _LOGGER.error("Error turning off %s: %s", self._device_name, ex, exc_info=True)
    
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
            
            # Power is a boolean directly
            if "Power" in device_params:
                power_state = device_params["Power"]
                self._attr_is_on = bool(power_state)
                _LOGGER.debug("Power state: %s", power_state)
            
            # brightness is an integer directly (range 1-100)
            if "brightness" in device_params:
                brightness = device_params["brightness"]
                self._attr_brightness = brightness
                _LOGGER.debug("Brightness: %s", brightness)
                    
        except Exception as ex:
            _LOGGER.error("Failed to update %s: %s", self._device_name, ex, exc_info=True)