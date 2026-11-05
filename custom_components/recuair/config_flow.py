"""Config flow for Recuair."""
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import RecuairApi
from .const import DOMAIN, MODEL
from .identity import async_get_mac_for_host, async_update_entry_identity

_LOGGER = logging.getLogger(__name__)


def _device_title(device_name: str) -> str:
    """Include the supported model in a device's Home Assistant title."""
    if MODEL.casefold() in device_name.casefold():
        return device_name
    return f"{device_name} {MODEL}"


class RecuairConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Recuair config flow."""

    VERSION = 1

    async def _async_handle_discovered_device(
        self, host: str, mac_address: str, device_name: str
    ) -> ConfigFlowResult:
        """Identify a discovered device by its DHCP-reported MAC address."""
        await self.async_set_unique_id(mac_address)
        existing_entry = next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.unique_id == mac_address
                or entry.data.get(CONF_HOST) == host
                or entry.options.get(CONF_HOST) == host
                or entry.unique_id.casefold() == device_name.casefold()
            ),
            None,
        )
        if existing_entry is not None:
            async_update_entry_identity(self.hass, existing_entry, mac_address, host)
            return self.async_abort(reason="already_configured")

        self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        device_title = _device_title(device_name)
        self.context["title_placeholders"] = {"name": device_title}
        self._discovered_host = host
        self._discovered_device_title = device_title
        return await self.async_step_discovery_confirm()

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle device discovery from Home Assistant's DHCP integration."""
        host = discovery_info.ip
        session = async_create_clientsession(self.hass)
        device_data = await RecuairApi(host, session).get_data()
        device_name = (device_data or {}).get("device_name")
        if not device_name:
            return self.async_abort(reason="cannot_connect")
        return await self._async_handle_discovered_device(
            host, format_mac(discovery_info.macaddress), device_name
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a Recuair device discovered over mDNS."""
        host = discovery_info.host
        session = async_create_clientsession(self.hass)
        api = RecuairApi(host, session)
        device_data = await api.get_data()
        device_name = (device_data or {}).get("device_name")

        if not device_name:
            return self.async_abort(reason="cannot_connect")

        mac_address = await async_get_mac_for_host(self.hass, host)
        if mac_address is None:
            return self.async_abort(reason="mac_not_found")
        return await self._async_handle_discovered_device(
            host, mac_address, device_name
        )

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered Recuair device."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_SCAN_INTERVAL] < 60:
                errors["base"] = "min_scan_interval"
            else:
                return self.async_create_entry(
                    title=self._discovered_device_title,
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_SCAN_INTERVAL, default=60): int,
            }),
            description_placeholders={
                "model": self._discovered_device_title,
                "host": self._discovered_host,
            },
            errors=errors,
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            if user_input.get(CONF_SCAN_INTERVAL, 60) < 60:
                errors["base"] = "min_scan_interval"
            else:
                session = async_create_clientsession(self.hass)
                api = RecuairApi(user_input[CONF_HOST], session)
                try:
                    data = await api.get_data()
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    device_name = (data or {}).get("device_name")
                    if not device_name:
                        errors["base"] = "cannot_connect"
                    else:
                        mac_address = await async_get_mac_for_host(
                            self.hass, user_input[CONF_HOST]
                        )
                        if mac_address is None:
                            errors["base"] = "mac_not_found"
                        else:
                            await self.async_set_unique_id(mac_address)
                            existing_entry = next(
                                (
                                    entry
                                    for entry in self._async_current_entries()
                                    if entry.unique_id == mac_address
                                    or entry.data.get(CONF_HOST)
                                    == user_input[CONF_HOST]
                                    or entry.options.get(CONF_HOST)
                                    == user_input[CONF_HOST]
                                    or entry.unique_id.casefold()
                                    == device_name.casefold()
                                ),
                                None,
                            )
                            if existing_entry is not None:
                                async_update_entry_identity(
                                    self.hass,
                                    existing_entry,
                                    mac_address,
                                    user_input[CONF_HOST],
                                )
                                return self.async_abort(reason="already_configured")
                            self._abort_if_unique_id_configured()
                            return self.async_create_entry(
                                title=_device_title(device_name), data=user_input
                            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_SCAN_INTERVAL, default=60): int,
            }),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RecuairOptionsFlowHandler()


class RecuairOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Recuair options."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            if user_input.get(CONF_SCAN_INTERVAL, 60) < 60:
                errors["base"] = "min_scan_interval"
            else:
                try:
                    session = async_create_clientsession(self.hass)
                    api = RecuairApi(user_input[CONF_HOST], session)
                    data = await api.get_data()
                    if data and data.get("device_name"):
                        return self.async_create_entry(title="", data=user_input)
                    else:
                        errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        current_host = self.config_entry.options.get(
            CONF_HOST, self.config_entry.data.get(CONF_HOST, "")
        )
        current_scan = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, self.config_entry.data.get(CONF_SCAN_INTERVAL, 60)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan): int,
            }),
            errors=errors,
        )
