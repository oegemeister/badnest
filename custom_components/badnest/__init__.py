"""The example integration."""
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_TYPE, CONF_ISSUE_TOKEN, CONF_COOKIE, CONF_APIKEY
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {   
                vol.Required(CONF_TYPE) : vol.In(['nest', 'google']),
                vol.Optional(CONF_EMAIL, default=""): cv.string,
                vol.Optional(CONF_PASSWORD, default=""): cv.string,
                vol.Optional(CONF_ISSUE_TOKEN, default=""): cv.string,
                vol.Optional(CONF_COOKIE, default=""): cv.string,
                vol.Optional(CONF_APIKEY, default=""): cv.string
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass, config):
    if config.get(DOMAIN) is not None:
        conf_type = config[DOMAIN].get(CONF_TYPE)
        issue_token = config[DOMAIN].get(CONF_ISSUE_TOKEN)
        cookie = config[DOMAIN].get(CONF_COOKIE)
        api_key = config[DOMAIN].get(CONF_APIKEY)
        email = config[DOMAIN].get(CONF_EMAIL)
        password = config[DOMAIN].get(CONF_PASSWORD)
    else:
        conf_type = None
        email = None
        password = None
        issue_token = None
        cookie = None
        api_key = None

    from .api import NestAPI
    api = NestAPI(
        conf_type,
        email,
        password,
        issue_token,
        cookie,
        api_key
    )

    hass.data[DOMAIN] = api

    return True
