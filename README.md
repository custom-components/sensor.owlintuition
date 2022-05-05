# OWL Intuition

A set of sensors to integrate the OWL Intuition devices network

## Installation (for Linux or Hassio systems)

1. On the Home Assistant server, install the Terminal&SSH Add-On
2. In a terminal do the following to download the files, and put them in the right place and clean up afterwards
```
cd /config
mkdir temp_dir
cd temp_dir
git clone https://github.com/custom-components/sensor.owlintuition.git
cd sensor.owlintuition/custom_components
mv owlintuition /config/custom_components
cd /config
rm -rf temp_dir
```
3. Follow the documentation for using the integration - documentation in Home Assistant format available at [sensor.owlintuition.markdown](./sensor.owlintuition.markdown). (Note you may have to restart the HA server to get this to work)
4. (Optional) If using the Home Energy feature (introduced in Home Assistant 2021.8.0) and using the Owl Intuition in a Type 1 configuration, then you may want to create a grid power sensor by copying the [package](https://www.home-assistant.io/docs/configuration/packages/) file [owl_intuition.yaml](custom_components/owlintuition/owl_intuition.yaml) in to your `packages` directory. This will create sensors for the current grid usage and the running total for the day.

## Troubleshooting

Some discussion and troubleshooting about this integration took place in the [Home Assistant forum](https://community.home-assistant.io/t/owl-intuition-pv-home-assistant/).

In particular, if HA seems to not receive any data, a first step is to validate that OWL is effectively sending out UDP updates to the configured port, and that the data can be received from the HA end. The [snippet here](test/testowl.py) may help to check that (edit it to suit your needs).

## Changelog:

- 1.6 - 05/05/2022: ported Energy support to latest HA core releases [@shortbloke]
* 1.5 - 20/09/2021: added support for the Energy feature in HA, and included [@shortbloke] a templated sensor for the Grid consumption
* 1.4 - 05/05/2019: added resources.json and updated code layout following 'the great migration'
* 1.3 - 13/01/2019: included support for triphase on the old XML format [@hadjimanolisg]
* 1.2 - 30/11/2018: added electricity cost and last update time (in UTC) sensors
* 1.1 - 15/10/2018: improved battery sensors
* 1.0 - 07/10/2018: general refactoring of the code and added support for hot water and heating sensors, credits to @jchasey
* 0.2 - 13/07/2018: added support for the solar generators meters
* 0.1 - 17/03/2018: first edition, including support for the electricity meter only
