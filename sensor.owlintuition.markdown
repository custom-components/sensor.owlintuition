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

In order to use the OWL Intuition platform, you have to configure your OWL base station to push data to your Home Assistant. [Step-by-step description / screenshots to be added here]

To enable the OWL Intuition sensor, add the following lines to your `configuration.yaml`:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: owlintuition
    host: 192.168.1.1         # IP address that the NetworkOWL sends to (your Home Assistant IP)
    port: 4321                # Port number of above
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
    monitored_conditions:
      - electricity
      - heating
      - hot_water
```
