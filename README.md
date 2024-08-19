[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

Philips Air Purifier Home Assistant custom component with MQTT (for Encrypted CoAP devices).
Tested on AC2729/50

This component provide a basic UI interface for  AC2729/50 Philips Air Purifier.

![](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/raw/master/dashboard.png)

## Requirements:

- [py-air-control (https://github.com/rgerganov/py-air-control)](https://github.com/rgerganov/py-air-control)
- [CoAPthon3 (https://github.com/rgerganov/CoAPthon3)](https://github.com/rgerganov/CoAPthon3)

## Installation steps:

1. Add custom component to homeassitant
2. Add the device to configuration.yml
3. _pip3 install -U git+https://github.com/rgerganov/CoAPthon3_
4. Restart HA

## Usage:

```yaml
fan:
  - platform: philips-airpurifier-coap
    host: 192.168.0.17
    mqtt: 192.168.0.18
```

## Configuration variables:

| Field    | Value                      | Necessity  | Description                  |
| -------- | -------------------------- | ---------- | ---------------------------- |
| platform | `philips-airpurifier-coap` | _Required_ | The platform name.           |
| host     | 192.168.0.17               | _Required_ | IP address of your Purifier. |
| name     | Philips Air Purifier       | Optional   | Name of the Fan.             |
| mqtt     | 192.168.0.18               | Optional   | MQTT broker IP address       |

## Here you can find device id:

![](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/raw/master/device_id.png)

## Available functions:

- Get device attributes (MQTT)
- [Set fan speed (off, low, medium, high, turbo)](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/raw/master/device_detail.png)
- [Set device mode (Available in speed select: Auto / Silent)](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/raw/master/device_detail.png)
- Set target humidity
- Set function
- Set display brightness
- Set child lock state

## Available services:

##### fan.philips_air_purifier_coap_set_humidity:

&NewLine;
| Key       | Example                     | Possible values        | Description     |
| --------- | --------------------------- | ---------------------- | --------------- |
| entity_id | fan.purifier_and_humidifier |                        | Fan entity id   |
| humidity  | "50"                        | "40", "50", "60", "70" | Tartget humidity|

##### fan.philips_air_purifier_coap_function:

&NewLine;
| Key       | Example                     | Possible values | Description                                                         |
| --------- | --------------------------- | --------------- | ------------------------------------------------------------------- |
| entity_id | fan.purifier_and_humidifier |                 | Fan entity id                                                       |
| function  | "PH"                        | "P", "PH"       | Device mode (P = Purification, PH = Purification and Humidification)|

##### fan.philips_air_purifier_coap_light_brightness:

&NewLine;
| Key        | Example                     | Possible values              | Description                    |
| ---------- | --------------------------- | ---------------------------- | ------------------------------ |
| entity_id  | fan.purifier_and_humidifier |                              | Fan entity id                  |
| brightness | "25"                        | "0", "25", "50", "75", "100" | Device display light brightness|

##### fan.philips_air_purifier_coap_child_lock:

&NewLine;
| Key       | Example                     | Possible values        | Description      |
| --------- | --------------------------- | ---------------------- | ---------------- |
| entity_id | fan.purifier_and_humidifier |                        | Fan entity id    |
| state     | False                       | True, False            | Child lock state |

## MQTT topic:

| Topic                                          | Description     |
| ---------------------------------------------- | --------------- |
| philips-air-purifier-coap/DEVICE_ID/attributes | Attributes json |

## MQTT topic sensor usage:

```yaml
sensor:
  - platform: mqtt
    state_topic: 'philips-air-purifier-coap/DEVICE_ID/attributes'
    name: 'PM 2.5'
    unit_of_measurement: 'Index'
    icon: 'mdi:chart-line'
    value_template: '{{ value_json.pm25 }}'
```

## Examples:
- [scripts.yaml configuration](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/blob/master/examples/scripts.yaml)
- [sensors.yaml configuration](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/blob/master/examples/sensors.yaml)
- [mqtt attributes json](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/blob/master/examples/mqtt_attributes.json)

## Known issues:
- Water level attribute only takes 0 or 100 values (AC2729/50)
- Sometimes the device disconnecting from the network, but reconnect again 5-10m later
