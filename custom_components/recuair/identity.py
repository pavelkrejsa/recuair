"""Resolve Recuair MAC addresses from Home Assistant DHCP discovery."""
from __future__ import annotations

import re
from ipaddress import ip_address

from homeassistant.components import dhcp
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN

_MAC_PATTERN = re.compile(r"^[0-9a-f]{2}(?::[0-9a-f]{2}){5}$")


def _normalize_host(host: str) -> str:
    """Normalize an IP address for matching discovery sources."""
    try:
        return str(ip_address(host.strip("[]")))
    except ValueError:
        return host.casefold().rstrip(".")


async def async_get_mac_for_host(hass: HomeAssistant, host: str) -> str | None:
    """Return the MAC reported by Home Assistant DHCP discovery for a host."""
    normalized_host = _normalize_host(host)
    for service_info in dhcp.async_discovered_service_info(hass):
        if _normalize_host(service_info.ip) != normalized_host:
            continue
        mac_address = format_mac(service_info.macaddress)
        if _MAC_PATTERN.fullmatch(mac_address):
            return mac_address
    return None


def mac_connection(entry: ConfigEntry) -> set[tuple[str, str]]:
    """Return the registered MAC connection when the entry has a MAC ID."""
    if _MAC_PATTERN.fullmatch(entry.unique_id.casefold()):
        return {(dr.CONNECTION_NETWORK_MAC, entry.unique_id.casefold())}
    return set()


def migrate_sensor_entity_ids(
    hass: HomeAssistant, entry: ConfigEntry, mac_address: str
) -> None:
    """Keep one sensor registry entry per sensor when IDs move to the device MAC."""
    entity_registry = er.async_get(hass)
    sensor_entries = er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    )
    entries_by_key: dict[str, list[er.RegistryEntry]] = {}
    for sensor_entry in sensor_entries:
        if sensor_entry.platform != DOMAIN or sensor_entry.domain != "sensor":
            continue
        if "}_" in sensor_entry.unique_id:
            _, sensor_key = sensor_entry.unique_id.rsplit("}_", 1)
        else:
            mac_prefix = f"{mac_address.casefold()}_"
            if not sensor_entry.unique_id.casefold().startswith(mac_prefix):
                continue
            sensor_key = sensor_entry.unique_id[len(mac_prefix) :]
        if sensor_key:
            entries_by_key.setdefault(sensor_key, []).append(sensor_entry)

    normalized_mac = mac_address.casefold()
    for sensor_key, candidates in entries_by_key.items():
        canonical_unique_id = f"{normalized_mac}_{sensor_key}"
        keeper = next(
            (
                candidate
                for candidate in candidates
                if candidate.unique_id.casefold() == canonical_unique_id
            ),
            None,
        )
        if keeper is None:
            keeper = next(
                (
                    candidate
                    for candidate in candidates
                    if normalized_mac not in candidate.unique_id.casefold()
                ),
                candidates[0],
            )

        for candidate in candidates:
            if candidate.entity_id != keeper.entity_id:
                entity_registry.async_remove(candidate.entity_id)

        if keeper.unique_id != canonical_unique_id:
            entity_registry.async_update_entity(
                keeper.entity_id, new_unique_id=canonical_unique_id
            )


def async_update_entry_identity(
    hass: HomeAssistant,
    entry: ConfigEntry,
    mac_address: str,
    host: str,
) -> bool:
    """Move an existing name-based entry and device registry record to its MAC."""
    conflicting_entry = next(
        (
            other
            for other in hass.config_entries.async_entries(DOMAIN)
            if other.entry_id != entry.entry_id and other.unique_id == mac_address
        ),
        None,
    )
    if conflicting_entry is not None:
        return False

    previous_unique_id = entry.unique_id
    registry = dr.async_get(hass)
    previous_identifier = (DOMAIN, previous_unique_id)
    device = registry.async_get_device_by_identifier(previous_identifier, entry.entry_id)
    if device is not None:
        mac_device = registry.async_get_device_by_connection(
            (dr.CONNECTION_NETWORK_MAC, mac_address), entry.entry_id
        )
        if mac_device is not None and mac_device.id != device.id:
            return False
        new_identifiers = set(device.identifiers)
        if previous_unique_id != mac_address:
            new_identifiers.discard(previous_identifier)
            new_identifiers.add((DOMAIN, mac_address))
        new_connections = set(device.connections)
        new_connections.add((dr.CONNECTION_NETWORK_MAC, mac_address))
        if (
            new_identifiers != device.identifiers
            or new_connections != device.connections
        ):
            registry.async_update_device(
                device.id,
                new_identifiers=new_identifiers,
                new_connections=new_connections,
            )

    current_host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST))
    updated_data = {**entry.data, CONF_HOST: host}
    updated_options = dict(entry.options)
    if CONF_HOST in updated_options:
        updated_options[CONF_HOST] = host

    hass.config_entries.async_update_entry(
        entry,
        unique_id=mac_address,
        data=updated_data,
        options=updated_options,
    )
    if current_host != host and entry.state is ConfigEntryState.LOADED:
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
    return True
