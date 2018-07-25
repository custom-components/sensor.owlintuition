"""
Support for QNAP shares.

The .ini file including the reported data must be directly accessible
on the file system. No remote connection is established.

Author: Giuseppe Lo Presti
First release: 25 July 2018
"""

import asyncio
import configparser
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_PATH, CONF_RESOURCES)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'QNAP'

SENSOR_USED = 'used'
SENSOR_COUNT = 'count'

SENSOR_TYPES = {
    SENSOR_USED: ['Size', 'GiB', 'mdi:chart-pie'],
    SENSOR_COUNT: ['Files', None, 'mdi:counter'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PATH): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_RESOURCES):
        vol.All(cv.ensure_list, [cv.string]),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the QNAP Share sensors."""
    data = QnapShares(config.get(CONF_PATH))
    dev = []
    for r in config.get(CONF_RESOURCES):
        for st in SENSOR_TYPES:
            dev.append(QnapShareSensor(data, config.get(CONF_NAME), st, r))
    async_add_devices(dev, True)


class QnapShares:
    """A class to parse the data cached by QNAP at the given path"""

    def __init__(self, configfile):
        """Parse the given ini file. It is never reparsed again"""
        self._data = configparser.ConfigParser()
        self._data.read(configfile)

    def get(self, section, key):
        """Get the appropriate data for the given section and key"""
        try:
            if key == SENSOR_USED:
                return round(float(self._data.get(section, 'Used Size'))/1024/1024/1024, 1)
            elif key == SENSOR_COUNT:
                return int(self._data.get(section, 'File Count')) + \
                       int(self._data.get(section, 'Directory Count'))
            else:
                return None
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            _LOGGER.error("Error retrieving QNAP shares data: %s", e)
            return None


class QnapShareSensor(Entity):
    """Implementation of the QNAP Share sensors."""

    def __init__(self, data, sensor_name, sensor_type, resource_name):
        """Set all config values and get initial state. Note there's no update."""
        self._name = '{} {} {}'.format(
                sensor_name, resource_name.capitalize(),
                SENSOR_TYPES[sensor_type][0])
        self._sensor_type = sensor_type
        self._state = data.get(resource_name, sensor_type)

    @property
    def name(self):
        """Return the name of this sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return SENSOR_TYPES[self._sensor_type][1]

    @property
    def icon(self):
        """Return the icon for this entity."""
        return SENSOR_TYPES[self._sensor_type][2]

    @property
    def state(self):
        """Return the current value for this sensor."""
        return self._state
