# Philips Air Purifier (CoAP) for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)](https://github.com/adamcsk1/ha-airpurifier-coap/graphs/commit-activity)

<p align="center">
  <img src="https://raw.githubusercontent.com/adamcsk1/ha-airpurifier-coap/v1/examples/images/dashboard.png" alt="Dashboard" width="600">
</p>

Custom component for Home Assistant to control Philips Air Purifiers (Encrypted CoAP devices) with MQTT support.
**Tested on:** AC2729/50


## Features

- **Get Device Attributes**: Publishes state via MQTT.
- **Control Fan Speed**: Off, Low, Medium, High, Turbo.
- **Set Modes**: Auto, Silent, Allergen.
- **Humidity Control**: Set target humidity.
- **Function Control**: Purification only (P) or Purification + Humidification (PH).
- **Light Control**: Set display brightness.
- **Child Lock**: Toggle child lock.

## Requirements

- [CoAPthon3](https://github.com/rgerganov/CoAPthon3)

## Installation

1.  **Install the Component**: Add this custom component to Home Assistant (manually).
2.  **Configure**: Add the configuration to your `configuration.yaml`.
3.  **Install Dependency**: Run the following command on your Home Assistant host system:
    ```bash
    pip3 install -U git+https://github.com/rgerganov/CoAPthon3
    ```
    **Note:** This is necessary because the Home Assistant core shipped CoAPthon3 is not compatible with some Philips devices.
4.  **Restart**: Restart Home Assistant.

## Configuration

Add the following to your `configuration.yaml`:

```yaml
fan:
  - platform: philips-airpurifier-coap
    host: 192.168.0.17 # IP address of your Purifier
    mqtt: 192.168.0.18  # Optional - MQTT broker IP address
    name: Philips Air Purifier # Optional - Name of the Fan entity
```

### Finding your Device ID

You can find that in the device extra attribute list. Go to the Developer Tools page, then select your device and check the device states. [Example device attributes](https://raw.githubusercontent.com/adamcsk1/ha-airpurifier-coap/v1/examples/images/device_detail.png)

If you have an MQTT explorer, you could find that with it. The used topic is `philips-air-purifier-coap` and that topic will list your devices.

<p align="center">
  <img src="https://raw.githubusercontent.com/adamcsk1/ha-airpurifier-coap/v1/examples/images/device_id.png" alt="Device id" width="600">
</p>

## Services

### `fan.philips_air_purifier_coap_set_humidity`
Sets the target humidity.

| Key | Example | Possible Values | Description |
| :--- | :--- | :--- | :--- |
| `entity_id` | `fan.purifier_and_humidifier` | | Fan entity ID |
| `humidity` | `"50"` | `"40"`, `"50"`, `"60"`, `"70"` | Target humidity % |

### `fan.philips_air_purifier_coap_function`
Sets the operation function.

| Key | Example | Possible Values | Description |
| :--- | :--- | :--- | :--- |
| `entity_id` | `fan.purifier_and_humidifier` | | Fan entity ID |
| `function` | `"PH"` | `"P"`, `"PH"` | `P` = Purification, `PH` = Purification & Humidification |

### `fan.philips_air_purifier_coap_light_brightness`
Sets the display brightness.

| Key | Example | Possible Values | Description |
| :--- | :--- | :--- | :--- |
| `entity_id` | `fan.purifier_and_humidifier` | | Fan entity ID |
| `brightness` | `"25"` | `"0"`, `"25"`, `"50"`, `"75"`, `"100"` | Display brightness % |

### `fan.philips_air_purifier_coap_child_lock`
Toggles the child lock.

| Key | Example | Possible Values | Description |
| :--- | :--- | :--- | :--- |
| `entity_id` | `fan.purifier_and_humidifier` | | Fan entity ID |
| `state` | `False` | `True`, `False` | Child lock state |

## MQTT Integration

**Topic Structure:**
`philips-air-purifier-coap/DEVICE_ID/attributes`

### Sensor Configuration Example

```yaml
sensor:
  - state_topic: "philips-air-purifier-coap/DEVICE_ID/attributes"
    name: "Temperature (Airpurifier)"
    unit_of_measurement: "Celsius"
    icon: "mdi:thermometer"
    value_template: "{{ value_json.temperature }}"
```

## Examples

- [Dashboard Configuration](https://github.com/adamcsk1/ha-airpurifier-coap/blob/v1/examples/dashboard_example.yaml)
- [Scripts Configuration](https://github.com/adamcsk1/ha-airpurifier-coap/blob/v1/examples/scripts.yaml)
- [MQTT Configuration](https://github.com/adamcsk1/ha-airpurifier-coap/blob/v1/examples/mqtt.yaml)
- [MQTT attributes JSON](https://github.com/adamcsk1/ha-airpurifier-coap/blob/v1/examples/mqtt_attributes.json)

## Known Issues

- **Water Level**: The water level attribute only reports `0` or `100` on AC2729/50.
- **Connectivity**: The device may disconnect from the network but usually reconnects within 5-10 minutes.
