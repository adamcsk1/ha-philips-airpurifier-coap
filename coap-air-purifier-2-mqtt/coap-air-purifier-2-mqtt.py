import json
import yaml
import subprocess
import re
import logging
import paho.mqtt.client as mqtt
from threading import Timer

_BASE_TOPIC = 'coap-air-purifier-2-mqtt'
_STATE_TOPIC = 'stat'
_CMD_TOPIC = 'cmd'
_CMD_MAPS = {
  "power": {
    "OFF": "--pwr 0",
    "ON": "--pwr 1",
  },
  "mode": {
    "MODE_OFF": "--pwr 0",
    "MANUAL_SPEED_LOW": "--mode M --om 1",
    "MANUAL_SPEED_MEDIUM": "--mode M --om 2",
    "MANUAL_SPEED_HIGH": "--mode M --om 3",
    "MODE_TURBO": "--mode M --om t",
    "MODE_AUTO": "--mode P",
    "MODE_ALLERGEN": "--mode A",
    "MODE_SILENT": "--mode S",
  },
  "humidity": {
    "VALUE_40": "--rhset 40",
    "VALUE_50": "--rhset 50",
    "VALUE_60": "--rhset 60",
    "VALUE_70": "--rhset 70"
  },
  "function": {
    "P": "--func P",
    "PH": "--func PH"
  },
  "light_brightness": {
    "VALUE_0": "--aqil 0",
    "VALUE_25": "--aqil 25",
    "VALUE_50": "--aqil 50",
    "VALUE_75": "--aqil 75",
    "VALUE_100": "--aqil 100"
  },
  "child_lock": {
    "TRUE": "--cl True",
    "FALSE": "--cl False"
  },
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

with open('configuration.yml', 'r') as file:
  config = yaml.safe_load(file)

if 'mqtt' not in config or 'devices' not in config:
  raise ValueError("configuration.yml missing required sections: mqtt/devices")
if 'host' not in config['mqtt'] or 'port' not in config['mqtt']:
  raise ValueError("configuration.yml missing mqtt.host or mqtt.port")
if 'timers' not in config:
  config['timers'] = {}
if 'polling' not in config['timers']:
  config['timers']['polling'] = 5

_DEBUG_ENABLED = bool(config.get('debug', False))

if _DEBUG_ENABLED:
  logging.getLogger().setLevel(logging.DEBUG)

try:
  attributes = {}

  mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
  mqtt_client.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password'])

  def on_connect(client, userdata, flags, reason_code, properties):
    logging.info("Connected with result code %s", reason_code)
    client.subscribe(f"{_BASE_TOPIC}/{_CMD_TOPIC}/#")
    logging.debug(f"Subscribed to {_BASE_TOPIC}/{_CMD_TOPIC}/#")
    _send_attributes()

  def on_message(client, userdata, msg):
    try:
      logging.debug(f"Incoming message topic={msg.topic} payload={msg.payload}")
      parts = msg.topic.split("/")
      if len(parts) < 4 or parts[0] != _BASE_TOPIC or parts[1] != _CMD_TOPIC:
        logging.warning("Ignoring malformed topic: %s", msg.topic)
        return

      msg_device_id = parts[2]
      msg_action = parts[3]
      msg_value = msg.payload.decode().strip().upper()
      host = attributes.get(msg_device_id, {}).get("host")

      if not host:
        logging.warning("No host for device id %s, ignoring action %s", msg_device_id, msg_action)
        return

      if msg_action in _CMD_MAPS:
        _airctrl_by_map(host, _CMD_MAPS[msg_action], msg_value, msg_device_id, msg_action)
      else:
        logging.warning("Unknown action %s for device %s", msg_action, msg_device_id)
    except Exception as e:
      logging.exception("Unexpected error handling message %s", msg.topic)

  mqtt_client.on_connect = on_connect
  mqtt_client.on_message = on_message
  mqtt_client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)

  def _airctrl_by_map(host, command_map, key, device_id=None, action=None):
    try:
      if key in command_map:
        logging.debug(f"Running action={action} value={key} on host={host}")
        _airctrl(host, f" {command_map[key]} --debug")
      else:
        logging.warning("Unknown value %s for action %s (device %s)", key, action, device_id)
    except Exception as e:
      logging.exception("Unexpected error running command for %s/%s", device_id, action)

  def _airctrl(host, command = ''):
    try:
      logging.debug(f"Executing airctrl for host={host} command={command}")
      result = subprocess.run(
        f"airctrl --ipaddr {host} --protocol coap {command}",
        shell=True,
        capture_output=True,
        text=True,
        check=False,
      )
      if result.returncode != 0:
        logging.debug("airctrl exit=%s stderr=%s", result.returncode, result.stderr.strip())
        return ""
      return result.stdout
    except Exception as e:
      logging.exception("Unexpected error running airctrl command")

  def _get_attr_value(attribute_lines, key):
      try:
          pattern = re.compile(r"\[(" + re.escape(key) + r")\](.*): (.*)")
          match = pattern.search(attribute_lines)
          return match.group(3) if match else ""
      except Exception as e:
          return ""

  def _send_attributes():
    global attributes

    try:
      for device in config['devices']:
        logging.debug(f"Querying device at host={device['host']}")
        stdout = _airctrl(device['host'])

        if stdout:
          tmp_attributes = {}
          tmp_attributes["name"] = _get_attr_value(stdout, "name")
          tmp_attributes["type"] = _get_attr_value(stdout, "type")
          tmp_attributes["model_id"] = _get_attr_value(stdout, "modelid")
          tmp_attributes["sw_version"] = _get_attr_value(stdout, "swversion")
          tmp_attributes["fan_speed"] = _get_attr_value(stdout, "om")
          tmp_attributes["state"] = _get_attr_value(stdout, "pwr")
          tmp_attributes["child_lock"] = _get_attr_value(stdout, "cl")
          tmp_attributes["light_brightness"] = _get_attr_value(stdout, "aqil")
          tmp_attributes["buttons_light"] = _get_attr_value(stdout, "uil")
          tmp_attributes["mode"] = _get_attr_value(stdout, "mode")
          tmp_attributes["function"] = _get_attr_value(stdout, "func")
          tmp_attributes["target_humidity"] = _get_attr_value(stdout, "rhset")
          tmp_attributes["humidity"] = _get_attr_value(stdout, "rh")
          tmp_attributes["temperature"] = _get_attr_value(stdout, "temp")
          tmp_attributes["pm25"] =  _get_attr_value(stdout, "pm25")
          tmp_attributes["allergen_index"] = _get_attr_value(stdout, "iaql")
          # aqit Air quality notification threshold)
          tmp_attributes["used_index"] = _get_attr_value(stdout, "ddp")
          # rddp
          tmp_attributes["error"] = _get_attr_value(stdout, "err")
          tmp_attributes["water_level"] = _get_attr_value(stdout, "wl")
          tmp_attributes["hepa_filter_type"] = _get_attr_value(stdout, "fltt1")
          tmp_attributes["carbon_filter_type"] = _get_attr_value(stdout, "fltt2")
          tmp_attributes["pre_filter"] = _get_attr_value(stdout, "fltsts0")
          tmp_attributes["hepa_filter"] = _get_attr_value(stdout, "fltsts1")
          tmp_attributes["carbon_filter"] = _get_attr_value(stdout, "fltsts2")
          tmp_attributes["wick_filter"] = _get_attr_value(stdout, "wicksts")
          tmp_attributes["range"] = _get_attr_value(stdout, "range")
          tmp_attributes["runtime"] = _get_attr_value(stdout, "Runtime")
          tmp_attributes["wifi_version"] = _get_attr_value(stdout, "WifiVersion")
          tmp_attributes["product_id"] = _get_attr_value(stdout, "ProductId")
          tmp_attributes["device_id"] = _get_attr_value(stdout, "DeviceId")
          tmp_attributes["status_type"] = _get_attr_value(stdout, "StatusType")
          tmp_attributes["connect_type"] = _get_attr_value(stdout, "ConnectType")
          # others
          tmp_attributes["host"] = device['host']

          if tmp_attributes.get('device_id', '') != '':
            logging.debug(f"Publishing state for device_id={tmp_attributes['device_id']}")
            for index, key in enumerate(tmp_attributes):
              #if tmp_attributes[key] != attributes.get(tmp_attributes['device_id'], {}).get(key, None):
                mqtt_client.publish(f"{_BASE_TOPIC}/{_STATE_TOPIC}/{tmp_attributes['device_id']}/{key}", tmp_attributes[key])
            attributes[tmp_attributes['device_id']] = tmp_attributes
    except Exception as e:
      logging.exception("Unexpected error sending attributes")
    Timer(min(config['timers']['polling'], 900), _send_attributes).start()

  mqtt_client.loop_forever()
except Exception as e:
    logging.exception("Unexpected top-level error")
    exit(1)
