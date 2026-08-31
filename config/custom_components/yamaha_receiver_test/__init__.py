"""The Yamaha receiver test integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import YamahaUpdateCoordinator
from .receiver_system import Receiver

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Yamaha receiver test integration from a config entry."""
    receiver_url = f"http://{entry.data['host']}/YamahaRemoteControl/ctrl"
    receiver = await Receiver.async_create(hass, receiver_url)
    coordinator = YamahaUpdateCoordinator(hass, entry, receiver)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
