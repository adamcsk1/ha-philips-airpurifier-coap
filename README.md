# CoapAirPurifier2MQTT

Home Assistant add-on that bridges air purifiers (CoAP) to MQTT using `py-air-control`. It polls device attributes and accepts MQTT commands to control power, mode, humidity setpoint, function, light brightness, and child lock.

<p align="center">
  <img src="https://raw.githubusercontent.com/adamcsk1/ha-airpurifier-coap/refs/heads/master/assets/images/dashboard.png" alt="Dashboard" width="600">
</p>

### Information about V1.x.x

This repository was ported from the custom component perspective to a Home Assistant add-on bridge, which provides full device control via MQTT.
If you want to use the old custom component–based version, you can find it [here](https://github.com/adamcsk1/ha-airpurifier-coap/tree/v1?tab=readme-ov-file). However, keep in mind that it is no longer maintained.

## Features
- Discovers devices from your `configuration.yml` and publishes state to MQTT (`coap-air-purifier-2-mqtt/stat/<device_id>/<key>`).
- Listens for commands on `coap-air-purifier-2-mqtt/cmd/<device_id>/<action>` with predefined action/value maps.
- Optional debug logging via `debug: true` in configuration.

## Configuration
Place `coap-air-purifier-2-mqtt/configuration.yml` in your HA `config/` directory:

```yaml
mqtt:
  host: 192.168.1.2
  port: 1883
  user: mqtt-user
  password: mqtt-password
devices:
  - host: 192.168.1.3
debug: false
```

Supported command actions and values (topics use lowercase actions; payloads are uppercase values):
- `power`: `ON`, `OFF`
- `mode`: `MODE_OFF`, `MANUAL_SPEED_LOW`, `MANUAL_SPEED_MEDIUM`, `MANUAL_SPEED_HIGH`, `MODE_TURBO`, `MODE_AUTO`, `MODE_ALLERGEN`, `MODE_SILENT`
- `humidity`: `VALUE_40`, `VALUE_50`, `VALUE_60`, `VALUE_70`
- `function`: `P`, `PH`
- `light_brightness`: `VALUE_0`, `VALUE_25`, `VALUE_50`, `VALUE_75`, `VALUE_100`
- `child_lock`: `TRUE`, `FALSE`

## Installation
0. If you do not have an MQTT broker yet, please install one. In Home Assistant, go to the Settings / Add-ons / Add-on store (https://my.home-assistant.io/redirect/supervisor_store/)** and install the **[Mosquitto broker](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto)** add-on. Then configure and start it.
1. Go back to the Add-on Store, open the menu, click on Repositories, then add the repo URL
 `https://github.com/adamcsk1/ha-airpurifier-coap`, or simply click the button below.

   [![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fadamcsk1%2Fha-airpurifier-coap)
2. Install the “CoapAirPurifier2MQTT” add-on, provide `configuration.yml`, and start it.

## Finding your Device ID

Get an MQTT Explorer—you can use it to inspect your broker. The topic used is coap-air-purifier-2-mqtt, and under the stat subtopic you will find your devices listed.

<p align="center">
  <img src="https://raw.githubusercontent.com/adamcsk1/ha-airpurifier-coap/refs/heads/master/assets/images/mqtt-explorer.png" alt="MQTT Explorer" width="600">
</p>

## Debugging
- Set `debug: true` to enable verbose debug logs (Python logging DEBUG level).
- Runtime logs show MQTT actions, command dispatches, and attribute polling; unknown topics/payloads are warned.

## Notes
- Requires network access to the purifiers (`host_network: true` in add-on config).
- MQTT topics and payloads are case-sensitive as listed above. Invalid values are ignored with a warning.
- The add-on was tested with the Philips AC2729/50 air purifier.

## Examples

- [Dashboard Configuration](https://github.com/adamcsk1/ha-airpurifier-coap/blob/master/assets/dashboard.yaml)
- [MQTT Configuration](https://github.com/adamcsk1/ha-airpurifier-coap/blob/master/assets/mqtt.yaml)

## Known issues:
- The water level attribute only takes 0 or 100 values.
- The device may disconnect from the network, but reconnect again 5-10 minutes later.
- The CoAP device may occasionally respond slowly and skip commands.
