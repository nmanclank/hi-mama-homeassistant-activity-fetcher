"""Config flow for HiMama Activities."""
import logging
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .api import HiMamaApi, HiMamaApiError, HiMamaAuthError

_LOGGER = logging.getLogger(__name__)

class HiMamaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HiMama Activities."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            session = aiohttp.ClientSession()
            api = HiMamaApi(
                session,
                user_input["email"],
                user_input["password"],
                user_input["child_id"],
            )
            
            try:
                await api.async_login()
                await session.close()
                
                await self.async_set_unique_id(user_input["child_id"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"HiMama Child {user_input['child_id']}",
                    data=user_input,
                )

            except HiMamaAuthError:
                errors["base"] = "invalid_auth"
            except HiMamaApiError:
                _LOGGER.exception("Cannot connect to HiMama")
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            finally:
                if not session.closed:
                    await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("email"): str,
                vol.Required("password"): str,
                vol.Required("child_id"): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=120)
                ),
            }),
            errors=errors,
        )
