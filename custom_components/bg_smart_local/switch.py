"""Support for BG Smart Local Control switches."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _is_power_only_switch(device_params: Any) -> bool:
    """Return true for socket-style devices that expose power without brightness."""
    return (
        isinstance(device_params, dict)
        and "Power" in device_params
        and "brightness" not in device_params
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BG Smart switches from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    device = data["device"]
    coordinator = data["coordinator"]

    _LOGGER.debug("Setting up BG Smart Local switches")

    try:
        params = coordinator.data
        _LOGGER.info("Device params: %s", params)

        if not params:
            _LOGGER.error("No params found in device properties")
            return

        entities = []
        for device_name, device_params in params.items():
            if _is_power_only_switch(device_params):
                _LOGGER.info("Creating switch entity for socket: %s", device_name)
                entities.append(
                    BGSmartSwitch(coordinator, device, device_name, device_params, entry)
                )
            else:
                _LOGGER.debug("Skipping non-switch device: %s", device_name)

        if entities:
            _LOGGER.info("Adding %s switch entities", len(entities))
            async_add_entities(entities)
        else:
            _LOGGER.debug("No switch devices found in parameters")

    except Exception as ex:
        _LOGGER.error("Failed to set up switches: %s", ex, exc_info=True)


class BGSmartSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a BG Smart socket or power-only outlet."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device,
        device_name: str,
        device_params: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._device = device
        self._device_name = device_name

        friendly_name = device_params.get("Name", device_name)

        self._attr_unique_id = f"{entry.entry_id}_{device_name}_switch"
        self._attr_name = friendly_name

        self._update_from_params(device_params)

        _LOGGER.info(
            "Initialized switch: %s (device: %s) - Power: %s",
            friendly_name,
            device_name,
            self._attr_is_on,
        )

    def _update_from_params(self, device_params: dict) -> None:
        """Update entity state from device parameters."""
        self._attr_is_on = bool(device_params.get("Power", False))

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
                "%s updated from coordinator - Power: %s",
                self._device_name,
                self._attr_is_on,
            )
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        _LOGGER.debug("Turn on %s", self._device_name)

        try:
            success = await self._device.set_param(
                self._device_name,
                "Power",
                True,
            )

            if success:
                self._attr_is_on = True
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Successfully turned on %s", self._device_name)
            else:
                _LOGGER.error("Failed to turn on %s", self._device_name)

        except Exception as ex:
            _LOGGER.error(
                "Error turning on %s: %s",
                self._device_name,
                ex,
                exc_info=True,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        _LOGGER.debug("Turn off %s", self._device_name)

        try:
            success = await self._device.set_param(
                self._device_name,
                "Power",
                False,
            )

            if success:
                self._attr_is_on = False
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
                _LOGGER.info("Successfully turned off %s", self._device_name)
            else:
                _LOGGER.error("Failed to turn off %s", self._device_name)

        except Exception as ex:
            _LOGGER.error(
                "Error turning off %s: %s",
                self._device_name,
                ex,
                exc_info=True,
            )
