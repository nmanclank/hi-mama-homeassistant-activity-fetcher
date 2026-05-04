"""Config flow for HiMama Activities."""
import logging
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .api import HiMamaApi, HiMamaApiError, HiMamaAuthError, HiMamaNoChildrenError

_LOGGER = logging.getLogger(__name__)

class HiMamaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HiMama Activities."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._kids = []
        self._user_input = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            self._user_input = user_input
            session = aiohttp.ClientSession()
            api = HiMamaApi(
                session,
                user_input["email"],
                user_input["password"],
                None,
            )
            
            try:
                await api.async_login()
                self._kids = await api.async_get_kids()
                await session.close()
                
                return await self.async_step_select_kid()

            except HiMamaAuthError:
                errors["base"] = "invalid_auth"
            except HiMamaNoChildrenError:
                errors["base"] = "no_children_found"
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
            }),
            errors=errors,
        )

    async def async_step_select_kid(self, user_input=None):
        """Handle the step to select a child."""
        if user_input is not None:
            kid_id = user_input["kid"]
            kid_name = next((k["name"] for k in self._kids if k["id"] == kid_id), f"Child {kid_id}")

            await self.async_set_unique_id(kid_id)
            self._abort_if_unique_id_configured()
            
            data = {
                "email": self._user_input["email"],
                "password": self._user_input["password"],
                "child_id": kid_id,
                "child_name": kid_name,
                CONF_UPDATE_INTERVAL: user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            }

            return self.async_create_entry(
                title=f"{kid_name} Activities",
                data=data,
            )

        return self.async_show_form(
            step_id="select_kid",
            data_schema=vol.Schema({
                vol.Required("kid"): vol.In({k["id"]: k["name"] for k in self._kids}),
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=120)
                ),
            }),
        )
