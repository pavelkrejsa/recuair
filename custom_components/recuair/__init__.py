"""The Recuair integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RecuairApi
from .const import DOMAIN
from .coordinator import RecuairCoordinator
from .identity import (
    async_get_mac_for_host,
    async_update_entry_identity,
    mac_connection,
    migrate_sensor_entity_ids,
)

PLATFORMS = ["sensor", "select", "number", "light"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recuair from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Options override data
    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    mac_address = await async_get_mac_for_host(hass, host)
    if not mac_address and mac_connection(entry):
        mac_address = entry.unique_id.casefold()
    if mac_address and entry.unique_id != mac_address:
        async_update_entry_identity(hass, entry, mac_address, host)
        host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    if mac_address:
        migrate_sensor_entity_ids(hass, entry, mac_address)
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 60)
    )
    session = async_get_clientsession(hass)
    api = RecuairApi(host, session)
    coordinator = RecuairCoordinator(hass, api, scan_interval)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload integration when options change
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update - reload the integration."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
