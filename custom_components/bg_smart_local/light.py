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
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

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
    coordinator = data["coordinator"]
    
    _LOGGER.debug("Setting up BG Smart Local lights v0.1.8")
    
    try:
        # Get device parameters from coordinator
        params = coordinator.data
        _LOGGER.info("Device params: %s", params)
        
        if not params:
            _LOGGER.error("No params found in device properties")
            return
        
        # Filter to only create entities for actual dimmer devices
        entities = []
        for device_name, device_params in params.items():
            if isinstance(device_params, dict) and "Power" in device_params and "brightness" in device_params:
                _LOGGER.info("Creating light entity for dimmer: %s", device_name)
                entities.append(BGSmartDimmer(coordinator, device, device_name, device_params, entry))
            else:
                _LOGGER.debug("Skipping non-dimmer device: %s", device_name)
        
        if entities:
            _LOGGER.info("Adding %s light entities", len(entities))
            async_add_entities(entities)
        else:
            _LOGGER.warning("No dimmer devices found in parameters")
            
    except Exception as ex:
        _LOGGER.error("Failed to set up lights: %s", ex, exc_info=True)


class BGSmartDimmer(CoordinatorEntity, LightEntity):
    """Representation of a BG Smart Dimmer."""
    
    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        device, 
        device_name: str, 
        device_params: dict, 
        entry: ConfigEntry
    ) -> None:
        """Initialize the dimmer."""
        super().__init__(coordinator)
        
        self._device = device
        self._device_name = device_name
        
        # Use the "Name" parameter if available, otherwise use device_name
        friendly_name = device_params.get("Name", device_name)
        
        self._attr_unique_id = f"{entry.entry_id}_{device_name}"
        self._attr_name = friendly_name
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        
        # Set initial state from device_params
        self._update_from_params(device_params)
        
        _LOGGER.info(
            "Initialized dimmer: %s (device: %s) - Power: %s, Brightness: %s%%",
            friendly_name, device_name, self._attr_is_on, 
            int((self._attr_brightness / 255) * 100) if self._attr_brightness else 0
        )
    
    def _update_from_params(self, device_params: dict) -> None:
        """Update entity state from device parameters."""
        # Power is a boolean directly
        self._attr_is_on = bool(device_params.get("Power", False))
        
        # brightness is an integer directly (range 1-100)
        brightness_pct = device_params.get("brightness", 100)
        # Convert from 1-100 to 0-255
        self._attr_brightness = int((brightness_pct / 100) * 255)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and self._device_name in self.coordinator.data:
            device_params = self.coordinator.data[self._device_name]
            self._update_from_params(device_params)
            _LOGGER.debug(
                "%s updated from coordinator - Power: %s, Brightness: %s%%", 
                self._device_name, self._attr_is_on,
                int((self._attr_brightness / 255) * 100) if self._attr_brightness else 0
            )
        self.async_write_ha_state()
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        _LOGGER.debug("Turn on %s, brightness=%s", self._device_name, brightness)
        
        try:
            # Determine target brightness
            if brightness is not None:
                # Convert from 0-255 to 1-100 (device range)
                brightness_pct = max(1, int((brightness / 255) * 100))
            else:
                # No brightness specified - use current or default to 100%
                if self._attr_brightness is not None:
                    brightness_pct = max(1, int((self._attr_brightness / 255) * 100))
                else:
                    brightness_pct = 100
            
            _LOGGER.info("Setting %s: Power=True, brightness=%s%%", self._device_name, brightness_pct)
            
            # Set brightness first
            success = await self._device.set_param(
                self._device_name,
                "brightness",
                brightness_pct
            )
            
            if not success:
                _LOGGER.error("Failed to set brightness for %s", self._device_name)
                return
            
            # Ensure power is on
            success = await self._device.set_param(
                self._device_name,
                "Power",
                True
            )
            
            if not success:
                _LOGGER.error("Failed to turn on power for %s", self._device_name)
                return
            
            # Update state immediately (don't wait for coordinator)
            self._attr_is_on = True
            self._attr_brightness = int((brightness_pct / 100) * 255)
            self.async_write_ha_state()
            
            # Request coordinator refresh
            await self.coordinator.async_request_refresh()
            
            _LOGGER.info("Successfully turned on %s at brightness %s%%", 
                        self._device_name, brightness_pct)
            
        except Exception as ex:
            _LOGGER.error("Error turning on %s: %s", self._device_name, ex, exc_info=True)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        _LOGGER.debug("Turn off %s", self._device_name)
        
        try:
            success = await self._device.set_param(
                self._device_name,
                "Power",
                False
            )
            
            if success:
                # Update state immediately
                self._attr_is_on = False
                self.async_write_ha_state()
                
                # Request coordinator refresh
                await self.coordinator.async_request_refresh()
                
                _LOGGER.info("Successfully turned off %s", self._device_name)
            else:
                _LOGGER.error("Failed to turn off %s", self._device_name)
                
        except Exception as ex:
            _LOGGER.error("Error turning off %s: %s", self._device_name, ex, exc_info=True)