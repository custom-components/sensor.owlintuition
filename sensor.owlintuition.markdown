---
layout: page
title: "OWL Intuition Sensor"
description: "Instructions on how to integrate OWL Intuition sensors into Home Assistant."
date: 2018-07-20 00:00
sidebar: true
comments: false
sharing: true
footer: true
logo: OWL-logo.jpg
ha_category: Power
ha_iot_class: "Local Polling"
---

The `owlintuition` sensor platform consumes the information provided by an [OWL Intuition](http://www.theowl.com/index.php/owl-intuition/) device on your LAN.

In order to use the OWL Intuition platform, you have to either configure the HA sensor to listen for the base station's multicast packets (the device's default configuration) or configure your OWL base station to push data to your Home Assistant IP. How to do this (as of December 2020):
1. Login into https://www.owlintuition.com with your account
2. Click on System in the top bar
3. Scroll to the bottom of the pop-up to "Advanced Settings"
4. Select the ">" on the Setup Data Push line
5. Set the IP address to the *INTERNAL IP* of your Home Assistant system, select a port, and click save

To configure the OWL Intuition sensor to receive multicast data add the following lines to your `configuration.yaml`:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: owlintuition
    host: 192.168.1.1         # Your Home Assistant IP
    monitored_conditions:
      - electricity
```

To configure the OWL Intuition sensor to receive push data add the following lines to your `configuration.yaml`:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: owlintuition
    host: 192.168.1.1         # IP address that the NetworkOWL sends to (your Home Assistant IP)
    port: 4321                # Port number you specified to the OWL data push settings
    monitored_conditions:
      - electricity
```
By default only the electricity sensors will be monitored. The host parameter is generally not necessary and will default to `localhost`.

{% linkable_title Configuration variables %}

Currently, this platform supports electric probes and solar generators. For the electric clamps, triphase installations are supported as well and one needs to specify `mode: triphase` in the configuration (the default mode is `monophase`).

This platform exposes multiple sensors according to the monitored conditions. The type of conditions that can be monitored are:

- **electricity**: Electrical energy being used.
- **solar**: Solar power being generated and used.
- **heating**: Heating system.
- **hot_water**: Hot water system.

{% linkable_title Complete example %}

```yaml
sensor:
  - platform: owlintuition
    port: 4321
    host: 192.168.1.10
    mode: triphase
    cost_icon: 'mdi:currency-eur'
    cost_unit_of_measurement: EUR
    monitored_conditions:
      - electricity
      - heating
      - hot_water
```
