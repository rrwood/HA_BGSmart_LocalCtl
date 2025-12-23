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
    
    # Get device parameters to discover devices
    try:
        params = await device.get_params()
        
        # Create a light entity for each device in params
        entities = []
        for device_name in params.keys():
            entities.append(BGSmartDimmer(device, device_name, entry))
        
        if entities:
            async_add_entities(entities)
        else:
            _LOGGER.warning("No devices found in parameters")
    except Exception as ex:
        _LOGGER.error("Failed to set up lights: %s", ex)


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
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        success = await self._device.set_param(
            self._device_name,
            "Power",
            {"power": 0}
        )
        
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()
    
    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        try:
            params = await self._device.get_params()
            if self._device_name in params:
                device_params = params[self._device_name]
                
                # Check for Power parameter
                if "Power" in device_params:
                    self._attr_is_on = device_params["Power"].get("power", 0) == 1
                
                # Check for Brightness parameter
                if "Brightness" in device_params:
                    self._attr_brightness = device_params["Brightness"].get("brightness", 0)
                    
        except Exception as ex:
            _LOGGER.error("Failed to update device state: %s", ex)