---
layout: page
title: "Somfy Tahoma Cover"
description: "Instructions how to integrate Somfy Tahoma covers within Home Assistant."
date: 2017-06-27 18:00
sidebar: true
comments: false
sharing: true
footer: true
logo: somfy.png
ha_category: Cover
ha_release: 0.48
ha_iot_class: "Assumed State"
---


The `somfytahoma` cover platform lets you control [Tahoma](http://www.tahomalink.com/) Somfy covers such as rollershutters through Home Assistant.

To enable Somfy Tahoma Covers in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
cover:
  - platform: somfytahoma
    username: UseYourLogin@tahomalink.com
    password: yourTahomaPassword
    filename: /path/to/cookiefile
```

Configuration variables:

- **username** (*Required*): Your Tahomalink account username.
- **password** (*Required*): Your Tahomalink account password.
- **filename** (*Optional*): A location to store a session cookie, to avoid to re-login at
  each action. Defaults to `tahomacookie`.

This platform is based on the unofficial [Python bindings for Tahoma](https://github.com/manuelciosici/TahomaProtocol), credits to the original authors. It currently only uses part of the protocol: all registered devices (either Somfy or IO-homecontrol) are auto-discovered, but scenarios and other features of the Tahoma box are ignored.
