"""Philips Air Purifier & Humidifier (CoAP)"""
import subprocess
import time
import paho.mqtt.client as mqtt
import logging
import json
import voluptuous as vol
import re
from datetime import datetime
from homeassistant.helpers import config_validation as cv, service
from homeassistant.components.fan import FanEntity, PLATFORM_SCHEMA, SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SPEED_OFF, SUPPORT_SET_SPEED

_LOGGER = logging.getLogger(__name__)
_MQTT_CLIENT = mqtt.Client(__name__)

__version__ = "0.1.6"

CONF_HOST = "host"
CONF_NAME = "name"
CONF_MQTT = "mqtt"

DOMAIN = "philips-air-purifier-coap"
DEFAULT_NAME = "Philips AirPurifier"
ICON = "mdi:air-purifier"
SERVICE_PREFIX = "philips_air_purifier_coap_set"

MODE_ALLERGEN = "allergen"
MODE_AUTO = "auto"
SPEED_TURBO = "turbo"
SPEED_SILENT = "silent"
HUMIDITY_OPTIONS = ["40","50","60","70"]
FUNCTION_OPTIONS = ["P","PH"]
BRIGHTNESS_OPTIONS = ["0","25","50","75","100"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MQTT): cv.string
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([PhilipsAirPurifierCoapFan(hass, config)])

class PhilipsAirPurifierCoapFan(FanEntity):
    def __init__(self, hass, config):
        self.hass = hass
        self._host = config[CONF_HOST]
        self._name = config[CONF_NAME]
        self._mqtt_host = config[CONF_MQTT]
        self._cmd = "airctrl --ipaddr " + self._host + " --protocol coap";
        self._attr = {}
        self._online = False
        self._inf_loop = 0
        self._update_counter = 0

        hass.services.register("fan", SERVICE_PREFIX+"_humidity", self.set_humidity, schema = vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("humidity"): vol.In(HUMIDITY_OPTIONS)
        }))

        hass.services.register("fan", SERVICE_PREFIX+"_function", self.set_function, schema = vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("function"): vol.In(FUNCTION_OPTIONS)
        }))

        hass.services.register("fan", SERVICE_PREFIX+"_light_brightness", self.set_light_brightness, schema = vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("brightness"): vol.In(BRIGHTNESS_OPTIONS)
        }))

        hass.services.register("fan", SERVICE_PREFIX+"_child_lock", self.set_child_lock, schema = vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("state"): cv.boolean
        }))

    def _mqtt_send(self, key, value):
        try:
            if self._attr["device_id"] and self._mqtt_host:
                _MQTT_CLIENT.connect(self._mqtt_host)
                _MQTT_CLIENT.publish(DOMAIN + "/" + self._attr["device_id"] + '/' + key, value)
                _MQTT_CLIENT.disconnect()
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))

    def _run(self, command):
        try:
            return subprocess.check_output(command, shell=True).decode('UTF-8')
        except Exception as e:
            msg = "Unexpected error: {}".format(e)
            if re.compile("(.*) ('airctrl --ipaddr) (.*) (--protocol coap' returned non-zero exit status 1.)").match(msg):
                _LOGGER.error("Unable to update device " + self._host + ", " + self._name + ": Airpurifier closed the connection.")
            elif re.compile("(.*) ('ping) (.*) (-c 1' returned non-zero exit status 1.)").match(msg):
                 _LOGGER.error(self._host + " offline")
            else:
                _LOGGER.error(msg)

    def _device_available(self):
        try:
            stdout = self._run("ping " + self._host + " -c 1")

            if stdout:
                if stdout.find('1 packets received') == -1:
                    self._online = False
                    _LOGGER.error(self._host + " offline")
                else:
                    self._online = True
            else:
                self._online = False
        except Exception as e:
            _LOGGER.error(self._host + " offline")
            self._online = False

    def _action_send_failed(self, stdout):
        try:
            if stdout.find('failed') == -1 or self._inf_loop > 10:
                if self._inf_loop  > 10:
                    _LOGGER.error("inf request resend loop")
                self._inf_loop = 0
                return False
            self._inf_loop = self._inf_loop + 1;
            _LOGGER.error("request send failed (waiting for resend)")
            time.sleep(0.5)
            return True
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))
            self._inf_loop = 0
            return False
        

    def turn_on(self, speed: str = None, **kwargs) -> None:
        if speed is None:
            stdout = self._run(self._cmd + " --pwr 1 --debug")
        else:
            stdout = self.set_speed(speed)

        if self._action_send_failed(stdout):
            self.turn_on(speed)
        else:
            self._update_attributes()

    def turn_off(self, **kwargs) -> None:
        stdout = self._run(self._cmd + " --pwr 0 --debug")

        if self._action_send_failed(stdout):
            self.turn_off()
        else:
            self._update_attributes()

    def set_speed(self, speed: str):
        if self._online == False:
            return ""
        if speed == SPEED_OFF:
            stdout = self._run(self._cmd + " --pwr 0 --debug")
        if speed == SPEED_LOW:
            stdout = self._run(self._cmd + " --mode M --om 1 --debug")
        if speed == SPEED_MEDIUM:
            stdout = self._run(self._cmd + " --mode M --om 2 --debug")
        if speed == SPEED_HIGH:
            stdout = self._run(self._cmd + " --mode M --om 3 --debug")
        if speed == SPEED_TURBO:
            stdout = self._run(self._cmd + " --mode M --om t --debug")
        if speed == MODE_AUTO:
            stdout = self._run(self._cmd + " --mode P --debug")
        if speed == MODE_ALLERGEN:
            stdout = self._run(self._cmd + " --mode A --debug")
        if speed == SPEED_SILENT:
            stdout = self._run(self._cmd + " --mode S --debug")
        return stdout

    def set_humidity(self, call):
        if self.entity_id == call.data.get("entity_id"):
            stdout = self._run(self._cmd + " --rhset " + call.data.get("humidity") + " --debug")

            if self._action_send_failed(stdout):
                self.set_humidity(call)
            else:
                self._update_attributes()

    def set_function(self, call):
        if self.entity_id == call.data.get("entity_id"):
            stdout = self._run(self._cmd + " --func " + call.data.get("function") + " --debug")

            if self._action_send_failed(stdout):
                self.set_function(call)
            else:
                self._update_attributes()

    def set_light_brightness(self, call):
        if self.entity_id == call.data.get("entity_id"):
            stdout = self._run(self._cmd + " --aqil " + call.data.get("brightness") + " --debug")

            if self._action_send_failed(stdout):
                self.set_light_brightness(call)
            else:
                self._update_attributes()

    def set_child_lock(self, call):
        if self.entity_id == call.data.get("entity_id"):
            if call.data.get("state") == True:
                cl = "True"
            else:
                cl = "False"

            stdout = self._run(self._cmd + " --cl " + cl + " --debug")

            if self._action_send_failed(stdout):
                self.set_child_lock(call)
            else:
                self._update_attributes()

    def _get_attr_value(self, attribute_lines, key):
        try:
            return re.compile("\[("+key+")\](.*): (.*)").search(attribute_lines).group(3)
        except Exception as e:
            return ""

    def _update_attributes(self):
        try:
            if self._online == False:
                return {}

            stdout = self._run(self._cmd)

            if stdout:
                #_LOGGER.error("stdout: "+stdout)
                attribute_lines =  stdout
            else:
                return {}

            self._attr["name"] = self._get_attr_value(attribute_lines, "name")
            self._attr["type"] = self._get_attr_value(attribute_lines, "type")
            self._attr["model_id"] = self._get_attr_value(attribute_lines, "modelid")
            self._attr["sw_version"] = self._get_attr_value(attribute_lines, "swversion")
            self._attr["fan_speed"] = self._get_attr_value(attribute_lines, "om")
            self._attr["state"] = self._get_attr_value(attribute_lines, "pwr")
            self._attr["child_lock"] = self._get_attr_value(attribute_lines, "cl")
            self._attr["light_brightness"] = self._get_attr_value(attribute_lines, "aqil")
            self._attr["buttons_light"] = self._get_attr_value(attribute_lines, "uil")
            self._attr["mode"] = self._get_attr_value(attribute_lines, "mode")
            self._attr["function"] = self._get_attr_value(attribute_lines, "func")
            self._attr["target_humidity"] = self._get_attr_value(attribute_lines, "rhset")
            self._attr["humidity"] = self._get_attr_value(attribute_lines, "rh")
            self._attr["temperature"] = self._get_attr_value(attribute_lines, "temp")
            self._attr["pm25"] =  self._get_attr_value(attribute_lines, "pm25")
            self._attr["allergen_index"] = self._get_attr_value(attribute_lines, "iaql")
            #aqit Air quality notification threshold)
            self._attr["used_index"] = self._get_attr_value(attribute_lines, "ddp")
            #rddp
            self._attr["error"] = self._get_attr_value(attribute_lines, "err")
            self._attr["water_level"] = self._get_attr_value(attribute_lines, "wl")
            self._attr["hepa_filter_type"] = self._get_attr_value(attribute_lines, "fltt1")
            self._attr["carbon_filter_type"] = self._get_attr_value(attribute_lines, "fltt2")
            self._attr["pre_filter"] = self._get_attr_value(attribute_lines, "fltsts0")
            self._attr["hepa_filter"] = self._get_attr_value(attribute_lines, "fltsts1")
            self._attr["carbon_filter"] = self._get_attr_value(attribute_lines, "fltsts2")
            self._attr["wick_filter"] = self._get_attr_value(attribute_lines, "wicksts")
            self._attr["range"] = self._get_attr_value(attribute_lines, "range")
            self._attr["runtime"] = self._get_attr_value(attribute_lines, "Runtime")
            self._attr["WifiVersion"] = self._get_attr_value(attribute_lines, "WifiVersion")
            self._attr["ProductId"] = self._get_attr_value(attribute_lines, "ProductId")
            self._attr["device_id"] = self._get_attr_value(attribute_lines, "DeviceId")
            self._attr["StatusType"] = self._get_attr_value(attribute_lines, "StatusType")
            self._attr["ConnectType"] = self._get_attr_value(attribute_lines, "ConnectType")
            self._attr["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self._mqtt_send("attributes", json.dumps(self._attr))
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))

    def update(self):
        self._update_counter = self._update_counter + 1
        
        if self._update_counter % 2 == 0:
            self._device_available()
            self._update_attributes()

    @property
    def speed(self):
        try:
            if self._online == False:
               return None
            if self._attr["mode"] == MODE_AUTO:
                return MODE_AUTO
            if self._attr["mode"] == MODE_ALLERGEN:
                return MODE_ALLERGEN
            if self._attr["fan_speed"] == "0":
                return SPEED_OFF
            if self._attr["fan_speed"] == "1":
                return SPEED_LOW
            if self._attr["fan_speed"] == "2":
                return SPEED_MEDIUM
            if self._attr["fan_speed"] == "3":
                return SPEED_HIGH
            if self._attr["fan_speed"] == SPEED_TURBO:
                return SPEED_TURBO
            if self._attr["fan_speed"] == SPEED_SILENT:
                return SPEED_SILENT
            return None
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))
            return None

    @property
    def fan_speed(self):
        return self.speed()

    @property
    def state(self):
        try:
            if self._online == False:
               return None
            if self._attr["state"] == "ON":
                return "on"
            else:
                return "off"
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))
            return None

    @property
    def device_state_attributes(self):
        return self._attr

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return ICON

    @property
    def supported_features(self) -> int:
        return SUPPORT_SET_SPEED

    @property
    def speed_list(self):
        return [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH, SPEED_TURBO, MODE_ALLERGEN, MODE_AUTO, SPEED_SILENT]
