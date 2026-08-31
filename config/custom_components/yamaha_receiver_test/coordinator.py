"""Coordinator for the Yamaha receiver test integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class YamahaUpdateCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Coordinate Yamaha receiver zone state updates."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, receiver
    ) -> None:
        """Initialize the coordinator."""
        self.receiver = receiver
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="YamahaReceiverTest",
            update_interval=timedelta(seconds=1),
            always_update=True,
        )

    async def _async_update_data(self) -> dict[str, object]:
        """Refresh the Yamaha receiver zone state."""
        await self.receiver.update_zones_statuses()
        return {
            "main_zone": self.receiver.main_zone,
            "zone_two": self.receiver.zone_two,
            "zone_three": self.receiver.zone_three,
        }
