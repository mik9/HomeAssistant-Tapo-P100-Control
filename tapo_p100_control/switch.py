"""Tapo P100 Plug Home Assistant Integration"""
import logging

from PyP100 import PyP100
import voluptuous as vol
from base64 import b64decode

import homeassistant.helpers.config_validation as cv

from homeassistant.components.switch import (
    SwitchEntity,
    PLATFORM_SCHEMA,
    SwitchDeviceClass,
    )
from homeassistant.const import CONF_IP_ADDRESS, CONF_EMAIL, CONF_PASSWORD

import json

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    ipAddress = config[CONF_IP_ADDRESS]
    email = config[CONF_EMAIL]
    password = config.get(CONF_PASSWORD)

    # Setup connection with devices/cloud
    p100 = PyP100.P100(ipAddress, email, password)

    try:
        p100.handshake()
        p100.login()
    except:
        _LOGGER.error("Could not connect to plug. Possibly invalid credentials")

    add_entities([P100Plug(ipAddress, email, password)])

class P100Plug(SwitchEntity):
    """Representation of a P100 Plug"""

    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, ipAddress, email, password):
        self.ipAddress = ipAddress
        self.email = email
        self.password = password

        self.__p100_handshake_login()
        
        self._name = "Tapo P100 Plug"
        self.update()

    def __p100_handshake_login(self):
        self._p100 = PyP100.P100(self.ipAddress, self.email, self.password)

        try:
            self._p100.handshake()
            self._p100.login()

            self._attr_available = True
        except:
            _LOGGER.error("Could not connect to plug. Possibly invalid credentials")
            self._attr_available = False
            return

        self.update()

    def __relogin_if_needed(func):
        def wrapped(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except:
                _LOGGER.warn("Could not connect to plug. Trying to relogin", exc_info=True)
                self.__p100_handshake_login()

                func(self, *args, **kwargs)
        
        return wrapped

    @property
    def name(self):
        """Name of the device."""
        return self._name

    @property
    def unique_id(self):
        """Unique id."""
        return self._unique_id

    @__relogin_if_needed
    def turn_on(self, **kwargs) -> None:
        """Turn Plug On"""

        self._p100.turnOn()
        self._attr_is_on = True

    @__relogin_if_needed
    def turn_off(self, **kwargs):
        """Turn Plug Off"""

        self._p100.turnOff()
        self._attr_is_on = False

    @__relogin_if_needed
    def update(self):
        data = self._p100.getDeviceInfo()

        encodedName = data["result"]["nickname"]
        name = b64decode(encodedName)
        self._name = name.decode("utf-8")

        self._attr_is_on = data["result"]["device_on"]
        self._unique_id = data["result"]["device_id"]
