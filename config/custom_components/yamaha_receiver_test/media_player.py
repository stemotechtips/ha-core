"""Media player entities for each Yamaha receiver zone."""

from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import YamahaUpdateCoordinator
from .receiver_system import Zone

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one HA media player per Yamaha zone."""
    coordinator: YamahaUpdateCoordinator = config_entry.runtime_data
    async_add_entities(
        [
            YamahaZoneEntity(coordinator, "main_zone"),
            YamahaZoneEntity(coordinator, "zone_two"),
            YamahaZoneEntity(coordinator, "zone_three"),
        ]
    )


class YamahaZoneEntity(CoordinatorEntity[YamahaUpdateCoordinator], MediaPlayerEntity):
    """Represent a Yamaha receiver zone as a Home Assistant media player."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, coordinator: YamahaUpdateCoordinator, zone_key: str) -> None:
        """Initialize the zone entity."""
        super().__init__(coordinator)
        self._zone_key = zone_key
        self._zone: Zone = coordinator.data[zone_key]
        self._attr_name = self._zone.zone_name.replace("_", " ")
        self._attr_unique_id = self._zone.zone_id

    @property
    def zone(self) -> Zone:
        """Return the underlying Yamaha zone."""
        return self.coordinator.data[self._zone_key]

    @property
    def receiver_ip(self) -> str:
        """Return the Yamaha receiver IP address from the coordinator-owned receiver."""
        return self.coordinator.receiver.ip_address

    @property
    def receiver(self):
        """Return the coordinator-owned Yamaha receiver."""
        return self.coordinator.receiver

    @property
    def state(self) -> MediaPlayerState:
        """Return the zone's power state."""
        return (
            MediaPlayerState.ON
            if getattr(self.zone, "is_on", False)
            else MediaPlayerState.OFF
        )

    @property
    def available(self) -> bool:
        """Return whether this zone is available."""
        return bool(getattr(self.zone, "exists", False))

    @property
    def source(self) -> str | None:
        """Return the current source/input for the zone."""
        input_status = getattr(self.zone, "input_status", None)
        if input_status is None:
            return None
        return getattr(input_status, "selected_input_title", None) or getattr(
            input_status, "selected_input", None
        )

    @property
    def volume_level(self) -> float | None:
        """Return the current volume as a normalized 0..1 value."""
        volume_status = getattr(self.zone, "volume_status", None)
        if volume_status is None:
            return None

        current = getattr(volume_status, "volume_level", None)
        if current is None:
            return None

        min_volume = -805
        max_volume = 165
        normalized = (current - min_volume) / (max_volume - min_volume)
        return max(0.0, min(1.0, normalized))

    @property
    def is_volume_muted(self) -> bool:
        """Return whether the zone is muted."""
        volume_status = getattr(self.zone, "volume_status", None)
        if volume_status is None:
            return False
        return bool(getattr(volume_status, "is_mute", False))

    @property
    def source_list(self) -> list[str] | None:
        """Return list of available input sources."""
        available_inputs = getattr(self.zone, "available_inputs", None)
        if available_inputs is None:
            return None
        return [input.name for input in available_inputs]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn on the zone."""
        receiver = self.receiver
        if receiver is not None:
            await self.zone.change_zone_power(receiver, True)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn off the zone."""
        receiver = self.receiver
        if receiver is not None:
            await self.zone.change_zone_power(receiver, False)
            await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume_level: float) -> None:
        """Set the zone volume."""
        receiver = self.receiver
        if receiver is None:
            return

        min_volume = -805
        max_volume = 165
        new_volume = round(min_volume + (max_volume - min_volume) * volume_level)
        await self.zone.change_zone_volume(receiver, new_volume)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_mute(self, mute: bool) -> None:
        """Mute or unmute the zone."""
        receiver = self.receiver
        zone = self.zone
        if receiver is not None and zone is not None:
            try:
                await zone.change_zone_mute(receiver, mute)
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Failed to set mute: %s", err)
        else:
            _LOGGER.warning("Cannot mute: receiver or zone is None")

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the zone (service handler)."""
        # Home Assistant calls this with the desired mute state
        await self.async_set_volume_mute(mute)

    def mute_volume(self, mute: bool = True) -> None:
        """Mute or unmute the zone (sync version for service compatibility).

        This method exists to satisfy Home Assistant's MediaPlayerEntity interface.
        The actual implementation is in async_mute_volume.
        """

    async def async_select_source(self, source: str) -> None:
        """Select an input source for the zone."""
        receiver = self.receiver
        if receiver is None:
            return

        # Find the Input_Type enum value that matches the source name
        available_inputs = getattr(self.zone, "available_inputs", [])
        selected_input = None
        for input_type in available_inputs:
            if input_type.name == source:
                selected_input = input_type
                break

        if selected_input is not None:
            await self.zone.change_zone_input(receiver, selected_input)
            await self.coordinator.async_request_refresh()
        else:
            print(f"Source {source} not found in available inputs")

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the zone entity."""
        return self._attr_unique_id
