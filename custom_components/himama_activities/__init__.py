"""The HiMama Activities integration."""
import asyncio
import logging
from datetime import timedelta
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, PLATFORMS, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .api import HiMamaApi, HiMamaApiError, HiMamaAuthError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HiMama Activities from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    email = entry.data["email"]
    password = entry.data["password"]
    child_id = entry.data["child_id"]

    session = aiohttp.ClientSession()
    api = HiMamaApi(session, email, password, child_id)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            # Login on each fetch cycle just to ensure session is valid
            await api.async_login()
            return await api.async_get_activities()
        except HiMamaAuthError as err:
            raise ConfigEntryAuthFailed from err
        except HiMamaApiError as err:
            raise UpdateFailed(f"Error communicating with HiMama: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    update_interval_minutes = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="himama_activities_sensor",
        update_method=async_update_data,
        update_interval=timedelta(minutes=update_interval_minutes),
    )
    
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "session": session
    }

    # This fixes the bug reported!
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id]["session"].close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
