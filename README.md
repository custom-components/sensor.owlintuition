# OWL Intuition
A set of sensors to integrate the OWL Intuition devices network

Installation (for Linux or Hassio systems)
1. On the Home Assitant server, install the Terminal&SSH Add-On
2. In Terminal do the following to download the files, and put them in the right place and clean up afterwards
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

## Changelog:
* 1.4 - 05/05/2019: added resources.json and updated code layout following 'the great migration'
* 1.3 - 13/01/2019: included support for triphase on the old XML format [@hadjimanolisg]
* 1.2 - 30/11/2018: added electricity cost and last update time (in UTC) sensors
* 1.1 - 15/10/2018: improved battery sensors
* 1.0 - 07/10/2018: general refactoring of the code and added support for hot water and heating sensors, credits to @jchasey
* 0.2 - 13/07/2018: added support for the solar generators meters
* 0.1 - 17/03/2018: first edition, including support for the electricity meter only
