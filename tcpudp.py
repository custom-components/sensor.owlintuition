"""
Support for TCP and UDP socket based sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.tcpudp/
"""
import logging
import socket
import select

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_MODE, CONF_HOST, CONF_PORT, CONF_PAYLOAD,
    CONF_TIMEOUT, CONF_UNIT_OF_MEASUREMENT, CONF_VALUE_TEMPLATE)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_BUFFER_SIZE = 'buffer_size'

DEFAULT_BUFFER_SIZE = 1024
DEFAULT_NAME = 'TCP-UDP Sensor'
DEFAULT_TIMEOUT = 10

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MODE): cv.string,
    vol.Optional(CONF_HOST, default=''): cv.string,
    vol.Required(CONF_PORT): cv.port,
    vol.Optional(CONF_PAYLOAD, default=''): cv.string,
    vol.Optional(CONF_BUFFER_SIZE, default=DEFAULT_BUFFER_SIZE):
        cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    vol.Optional(CONF_VALUE_ON): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the TCP-UDP Sensor."""
    add_devices([TcpUdpSensor(hass, config)])


class TcpUdpSensor(Entity):
    """Implementation of a TCP or UDP socket based sensor."""

    required = tuple()

    def __init__(self, hass, config):
        """Set all the config values if they exist and get initial state."""
        value_template = config.get(CONF_VALUE_TEMPLATE)

        if value_template is not None:
            value_template.hass = hass

        self._hass = hass
        self._config = {
            CONF_NAME: config.get(CONF_NAME),
            CONF_MODE: config.get(CONF_MODE),
            CONF_HOST: config.get(CONF_HOST),
            CONF_PORT: config.get(CONF_PORT),
            CONF_TIMEOUT: config.get(CONF_TIMEOUT),
            CONF_PAYLOAD: config.get(CONF_PAYLOAD),
            CONF_UNIT_OF_MEASUREMENT: config.get(CONF_UNIT_OF_MEASUREMENT),
            CONF_VALUE_TEMPLATE: value_template,
            CONF_VALUE_ON: config.get(CONF_VALUE_ON),
            CONF_BUFFER_SIZE: config.get(CONF_BUFFER_SIZE),
        }
        self._state = None
        self.update()

    @property
    def name(self):
        """Return the name of this sensor."""
        name = self._config[CONF_NAME]
        if name is not None:
            return name
        return super(TcpUdpSensor, self).name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def mode(self):
        """Return the mode (TCP or UDP) of this sensor."""
        return self._config[CONF_MODE]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return self._config[CONF_UNIT_OF_MEASUREMENT]

    def update(self):
        """Get the latest value for this sensor."""
        if mode.upper() == 'TCP':
            ...
        elif mode.upper() == 'UDP':
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self._config[CONF_TIMEOUT])
            try:
                sock.bind((socket.gethostbyname(socket.getfqdn()),
                           self._config[CONF_PORT]))
            except socket.error as err:
                _LOGGER.error("Unable to bind on port %s: %s",
                              self._config[CONF_PORT], err)
                return

            readable, _, _ = select.select(
                [sock], [], [], self._config[CONF_TIMEOUT])
            if not readable:
                _LOGGER.warning(
                    "Timeout (%s second(s)) waiting for data on port %s.",
                    self._config[CONF_TIMEOUT], self._config[CONF_PORT])
                return

            value = sock.recvfrom(self._config[CONF_BUFFER_SIZE]).decode()

        if self._config[CONF_VALUE_TEMPLATE] is not None:
            try:
                self._state = self._config[CONF_VALUE_TEMPLATE].render(
                    value=value)
                return
            except TemplateError as err:
                _LOGGER.error(
                    "Unable to render template of %r with value: %r",
                    self._config[CONF_VALUE_TEMPLATE], value)
                return

        self._state = value
