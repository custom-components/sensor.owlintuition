"""
Support for OWL Intuition Power Meter.

For more details about this platform, please refer to the documentation at
https://github.com/glpatcern/domotica/blob/master/homeass/code/sensor.owlintuition.markdown
"""

import asyncio
import socket
from xml.etree import ElementTree as ET
from datetime import timedelta
from select import select
from functools import reduce

import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_PORT,
    CONF_MONITORED_CONDITIONS, CONF_MODE, CONF_HOST)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'OWL Meter'
MODE_MONO = 'monophase'
MODE_TRI = 'triphase'

SENSOR_BATTERY = 'battery'
SENSOR_RADIO = 'radio'
SENSOR_POWER = 'power'
SENSOR_ENERGY_TODAY = 'energy_today'
SENSOR_SOLAR_GPOWER = 'solargen'
SENSOR_SOLAR_GENERGY_TODAY = 'solargen_today'
SENSOR_SOLAR_EPOWER = 'solarexp'
SENSOR_SOLAR_EENERGY_TODAY = 'solarexp_today'

OWL_CLASSES = ['weather', 'electricity', 'solar']

SENSOR_TYPES = {
    SENSOR_BATTERY: ['Battery', None, 'mdi:battery', 'electricity'],
    SENSOR_RADIO: ['Radio', 'dBm', 'mdi:signal', 'electricity'],
    SENSOR_POWER: ['Power', 'W', 'mdi:flash', 'electricity'],
    SENSOR_ENERGY_TODAY: ['Energy Today', 'kWh', 'mdi:flash', 'electricity'],
    SENSOR_SOLAR_GPOWER: ['Solar Generating', 'W', 'mdi:flash', 'solar'],
    SENSOR_SOLAR_GENERGY_TODAY: ['Solar Generated Today', 'kWh', 'mdi:flash', 'solar'],
    SENSOR_SOLAR_EPOWER: ['Solar Exporting', 'W', 'mdi:flash', 'solar'],
    SENSOR_SOLAR_EENERGY_TODAY: ['Solar Exported Today', 'kWh', 'mdi:flash', 'solar'],
}

DEFAULT_MONITORED = [SENSOR_BATTERY, SENSOR_POWER, SENSOR_ENERGY_TODAY]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.port,
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MODE, default=MODE_MONO):
        vol.In([MODE_MONO, MODE_TRI]),
    vol.Optional(CONF_MONITORED_CONDITIONS, default=DEFAULT_MONITORED):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})

SOCK_TIMEOUT = 60


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the OWL Intuition Sensors."""
    hostname = config.get(CONF_HOST)
    if hostname == 'localhost':
        # Perform a reverse lookup to make sure we listen to the correct IP
        hostname = socket.gethostbyname(socket.getfqdn())
    # Try and estimate an appropriate refresh interval: if only the electricity
    # module is present, 60 seconds is OK, otherwise double the rate.
    # All of this won't be needed with an async listener...
    nbclasses = len(reduce(lambda c, s: c | {SENSOR_TYPES[s][3]}, \
                           config.get(CONF_MONITORED_CONDITIONS), set()))
    owldata = OwlData((hostname, config.get(CONF_PORT)), \
                      timedelta(seconds=(60/nbclasses - 2)))

    # Ideally an async listener loop as follows would be a better solution,
    # but it crashes HA!
    #owljob = hass.loop.create_datagram_endpoint(
    #             lambda: OwlStateUpdater(hass.loop), \
    #             local_addr=(hostname, config.get(CONF_PORT)))
    #hass.async_add_job(owljob)

    dev = []
    for v in config.get(CONF_MONITORED_CONDITIONS):
        dev.append(OwlIntuitionSensor(owldata, config.get(CONF_NAME), v))
    if config.get(CONF_MODE) == MODE_TRI:
        for phase in range(1, 4):
            if SENSOR_POWER in config.get(CONF_MONITORED_CONDITIONS):
                dev.append(OwlIntuitionSensor(owldata, config.get(CONF_NAME),
                                              SENSOR_POWER, phase))
            if SENSOR_ENERGY_TODAY in config.get(CONF_MONITORED_CONDITIONS):
                dev.append(OwlIntuitionSensor(owldata, config.get(CONF_NAME),
                                              SENSOR_ENERGY_TODAY, phase))
    async_add_devices(dev, True)


class OwlData:
    """A class to retrieve data from the OWL station via UDP.

    The callback method can be used by an event loop in a thread-safe way
    when new data is received. However, async loops crash HA!
    The update() method is instead fully synchronous.
    """

    def __init__(self, localaddr, refreshinterval):
        """Prepare an empty dictionary"""
        self.data = {}
        self._localaddr = localaddr
        # Updates are sent every 60 seconds by each module
        self.update = Throttle(refreshinterval)(self._update)

    def _update(self):
        """Retrieve the latest data by listening to the periodic UDP message"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(SOCK_TIMEOUT)
            try:
                sock.bind(self._localaddr)
            except socket.error as se:
                _LOGGER.error("Unable to bind: %s", se)
                return

            readable, _, _ = select([sock], [], [], SOCK_TIMEOUT)
            if not readable:
                _LOGGER.warning(
                    "Timeout (%s second(s)) waiting for data on port %s.",
                    SOCK_TIMEOUT, self._config.get(CONF_PORT))
                return

            data, _ = sock.recvfrom(1024)
            self.on_data_received(data.decode('utf-8'))

    def on_data_received(self, xmldata):
        """Callback when new data is received: store it in the dict"""
        try:
            xml = ET.fromstring(xmldata)
            self.data[xml.tag] = xml
        except ET.ParseError as pe:
            _LOGGER.error("Unable to parse received data: %s", pe)

    def get(self, owlclass):
        """Facade for the internal dictionary's get method"""
        return self.data.get(owlclass)


class OwlIntuitionSensor(Entity):
    """Implementation of the OWL Intuition Power Meter sensors."""

    def __init__(self, owldata, sensor_name, sensor_type, phase=0):
        """Set all the config values if they exist and get initial state."""
        self._owldata = owldata
        if(phase > 0):
            self._name = '{} {} P{}'.format(
                sensor_name,
                SENSOR_TYPES[sensor_type][0],
                phase)
        else:
            self._name = '{} {}'.format(
                sensor_name,
                SENSOR_TYPES[sensor_type][0])
        self._sensor_type = sensor_type
        self._phase = phase
        self._owl_class = SENSOR_TYPES[sensor_type][3]
        self._state = None

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
        self._owldata.update()
        xml = self._owldata.get(self._owl_class)
        if xml is None:
            return
        # Electricity sensors
        if self._sensor_type == SENSOR_BATTERY:
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
        elif self._sensor_type == SENSOR_POWER:
            if self._phase == 0:
                self._state = int(float(xml.find('property').find('current').
                                  find('watts').text))
            else:
                self._state = int(float(xml.find('channels').
                                  findall('chan')[self._phase-1].
                                  find('curr').text))
        elif self._sensor_type == SENSOR_ENERGY_TODAY:
            if self._phase == 0:
                self._state = round(float(xml.find('property').find('day').
                                    find('wh').text)/1000, 2)
            else:
                self._state = round(float(xml.find('channels').
                                    findall('chan')[self._phase-1].
                                    find('day').text)/1000, 2)
        # Solar sensors
        elif self._sensor_type == SENSOR_SOLAR_GPOWER:
            self._state = int(float(xml.find('current').
                              find('generating').text))
        elif self._sensor_type == SENSOR_SOLAR_EPOWER:
            self._state = int(float(xml.find('current').
                              find('exporting').text))
        elif self._sensor_type == SENSOR_SOLAR_GENERGY_TODAY:
            self._state = round(float(xml.find('day').
                                find('generated').text)/1000, 2)
        elif self._sensor_type == SENSOR_SOLAR_EENERGY_TODAY:
            self._state = round(float(xml.find('day').
                                find('exported').text)/1000, 2)


class OwlStateUpdater(asyncio.DatagramProtocol):
    """An helper class for the async UDP listener loop.

    More info at:
    https://docs.python.org/3/library/asyncio-protocol.html"""

    def __init__(self, eloop):
        """Boiler-plate initialisation"""
        self.eloop = eloop
        self.transport = None

    def connection_made(self, transport):
        """Boiler-plate connection made metod"""
        self.transport = transport

    def datagram_received(self, packet, addr_unused):
        """Get the last received datagram and notify the
        OwlData singleton for storing it if relevant"""
        xmldata = packet.decode('utf-8')
        root = xmldata[1:xmldata.find(' ')]
        if root in OWL_CLASSES:
            # do not call here that method, but instead leave
            # the event loop do it when convenient AND thread-safe!
            self.eloop.call_soon_threadsafe(
                owldata.on_data_received, xmldata)
        else:
            _LOGGER.warning("Unsupported type '%s' in data: %s", \
                            root, packet)

    def error_received(self, exc):
        """Boiler-plate error received method"""
        _LOGGER.error("Received error %s", exc)

    def cleanup(self):
        """Boiler-plate cleanup method"""
        if self.transport:
            self.transport.close()
        self.transport = None
