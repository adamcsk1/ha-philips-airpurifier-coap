[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## Usage:
```yaml
fan:
  - platform: philips-airpurifier-coap
    host: 192.168.0.17
    mqtt: 192.168.0.18
```

## Configuration variables:
Field | Value | Necessity | Description
--- | --- | --- | ---
platform | `philips-airpurifier-coap` | *Required* | The platform name.
host | 192.168.0.17 | *Required* | IP address of your Purifier.
name | Philips Air Purifier | Optional | Name of the Fan.
mqtt | 192.168.0.18 | Optional | MQTT broker IP address
***

## MQTT topic:
Topic | Description
--- | ---
philips-air-purifier-coap/DEVICE_ID/attributes | Attributes json

## MQTT topic sensor usage:
```yaml
sensor:
  - platform: mqtt
    state_topic: "philips-air-purifier-coap/DEVICE_ID/attributes"
    name: "PM 2.5 (Airpurifier)"
    unit_of_measurement: "Index"
    icon: "mdi:chart-line"
    value_template: "{{ value_json.pm25 }}"
```

## Installation steps:
1. Add custom component to homeassitant
2. Add the device to configuration.yml
3. pip3 install py-air-control
4. pip3 install -U git+https://github.com/rgerganov/CoAPthon3
5. Restart HA

## Here you can find device id:
![](https://gitlab.com/adamcsk1-public/philips-airpurifier-coap/-/raw/master/device_id.png)