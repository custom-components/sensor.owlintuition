"""
Support for OWL Intuition Power Meter.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.owlintuition/
"""

import asyncio
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_PORT,
    CONF_MONITORED_CONDITIONS, CONF_MODE, CONF_HOST)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from xml.etree import ElementTree as ET
import socket

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'OWL Meter'
MODE_MONO = 'monophase'
MODE_TRI = 'triphase'

SENSOR_BATTERY = 'battery'
SENSOR_RADIO = 'radio'
SENSOR_POWER = 'power'
SENSOR_ENERGY_TODAY = 'energy_today'

SENSOR_TYPES = {
    SENSOR_BATTERY: ['Battery', None, 'mdi:battery'],
    SENSOR_RADIO: ['Radio', 'dBm', 'mdi:signal'],
    SENSOR_POWER: ['Power', 'W', 'mdi:flash'],
    SENSOR_ENERGY_TODAY: ['Energy Today', 'kWh', 'mdi:flash']
}

DEFAULT_MONITORED = [SENSOR_BATTERY, SENSOR_POWER, SENSOR_ENERGY_TODAY]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.port,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=DEFAULT_MONITORED):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MODE, default=MODE_MONO):
        vol.In([MODE_MONO, MODE_TRI]),
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the OWL Intuition Sensors."""
    data = OwlIntuitionData()

    dev = []
    for v in config.get(CONF_MONITORED_CONDITIONS):
        dev.append(OwlIntuitionSensor(config, v, data))
    if config.get(CONF_MODE) == MODE_TRI:
        for phase in range(1, 4):
            if SENSOR_POWER in config.get(CONF_MONITORED_CONDITIONS):
                dev.append(OwlIntuitionSensor(config, SENSOR_POWER,
                                              data, phase))
            if SENSOR_ENERGY_TODAY in config.get(CONF_MONITORED_CONDITIONS):
                dev.append(OwlIntuitionSensor(config, SENSOR_ENERGY_TODAY,
                                              data, phase))
    async_add_devices(dev, True)

    _hostname = config.get(CONF_HOST)
    if _hostname == 'localhost':
        # perform a reverse lookup to make sure we listen to the correct IP
        _hostname = socket.gethostbyname(socket.getfqdn())
    # create an UDP async listener loop and return it. Credits to @madpilot,
    # https://community.home-assistant.io/t/async-update-guidelines/51283/2
    owljob = hass.loop.create_datagram_endpoint( \
        lambda: StateUpdater(hass.loop, data), \
        local_addr=(_hostname, config.get(CONF_PORT)))
    return hass.async_add_job(owljob)


class OwlIntuitionSensor(Entity):
    """Implementation of the OWL Intuition Power Meter sensors."""

    def __init__(self, config, sensor_type, data, phase=0):
        """Set all the config values if they exist and get initial state."""
        self._sensor_type = sensor_type
        self._data = data
        self._phase = phase
        self._state = None
        if(phase > 0):
            self._name = '{} {} P{}'.format(
                config.get(CONF_NAME),
                SENSOR_TYPES[sensor_type][0],
                phase)
        else:
            self._name = '{} {}'.format(
                config.get(CONF_NAME),
                SENSOR_TYPES[sensor_type][0])

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

    def update(self):
        """Retrieve the latest value for this sensor."""
        xml = self._data.getXmlData()
        if xml is None or xml.find('property') is None:
            # no data yet or the update does not contain useful data:
            # keep the previous state
            return
        elif self._sensor_type == SENSOR_BATTERY:
            # strip off the '%'
            batt_lvl = int(xml.find("battery").attrib['level'][:-1])
            if batt_lvl > 90:
                self._state = 'High'
            elif batt_lvl > 30:
                self._state = 'Medium'
            elif batt_lvl > 10:
                self._state = 'Low'
            else:
                self._state = 'Very Low'
        elif self._sensor_type == SENSOR_RADIO:
            self._state = int(xml.find('signal').attrib['rssi'])
        elif self._phase == 0:
            if self._sensor_type == SENSOR_POWER:
                self._state = int(float(xml.find('property').find('current').
                                  find('watts').text))
            elif self._sensor_type == SENSOR_ENERGY_TODAY:
                self._state = round(float(xml.find('property').find('day').
                                    find('wh').text)/1000, 2)
        else:
            if self._sensor_type == SENSOR_POWER:
                self._state = int(float(xml.find('channels').
                                  findall('chan')[self._phase-1].
                                  find('curr').text))
            elif self._sensor_type == SENSOR_ENERGY_TODAY:
                self._state = round(float(xml.find('channels').
                                    findall('chan')[self._phase-1].
                                    find('day').text)/1000, 2)


class OwlIntuitionData(object):
    """Listen to updates via UDP from the OWL Intuition station"""

    def __init__(self):
        """Initialize the data gathering class"""
        self._xml = None

    def getXmlData(self):
        """Return the last retrieved full XML tree"""
        return self._xml

    def onPacketReceived(self, packet):
        """Callback when the UDP datagram is received"""
        try:
            self._xml = ET.fromstring(packet.decode('utf-8'))
        except ET.ParseError as pe:
            _LOGGER.error("Unable to parse received data %s: %s", packet, pe)


class StateUpdater(asyncio.DatagramProtocol):
    """An helper class for the async UDP listener

    More info at:
    https://docs.python.org/3/library/asyncio-protocol.html"""

    def __init__(self, loop, data):
        """Initialisation"""
        self.loop = loop
        self.data = data
        self.transport = None

    def connection_made(self, transport):
        """Boiler-plate connection made metod"""
        self.transport = transport

    def datagram_received(self, packet, addr):
        """Pass datagram to the OWL handler"""
        self.data.onPacketReceived(packet)

    def wait(self, device):
        """Boiler-plate wait method"""
        return self.data.wait_for_response(device, self.loop)

    def cleanup(self):
        """Boiler-plate cleanup method"""
        if self.transport:
            self.transport.close()
            self.transport = None
