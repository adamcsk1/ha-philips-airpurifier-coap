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
from homeassistant.components.fan import FanEntity, PLATFORM_SCHEMA, SUPPORT_PRESET_MODE

_LOGGER = logging.getLogger(__name__)
_MQTT_CLIENT = mqtt.Client(__name__)

__version__ = "0.1.9"

CONF_HOST = "host"
CONF_NAME = "name"
CONF_MQTT = "mqtt"
CONF_DEBUG = "debug"

DOMAIN = "philips-air-purifier-coap"
DEFAULT_NAME = "Philips AirPurifier"
ICON = "mdi:air-purifier"
SERVICE_PREFIX = "philips_air_purifier_coap_set"

MODE_ALLERGEN = "Allergen"
MODE_AUTO = "Auto"
MODE_TURBO = "Turbo"
MODE_SILENT = "Silent"
MANUAL_SPEED_HIGH = 'Manual speed high'
MANUAL_SPEED_LOW = 'Manual speed low' 
MANUAL_SPEED_MEDIUM = 'Manual speed medium'
MODE_OFF = 'Off'
HUMIDITY_OPTIONS = ["40","50","60","70"]
FUNCTION_OPTIONS = ["P","PH"]
BRIGHTNESS_OPTIONS = ["0","25","50","75","100"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MQTT): cv.string,
        vol.Optional(CONF_DEBUG, default=False): cv.boolean,
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
        self._debug = config[CONF_DEBUG]
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
                self.debug_log("Unable to update device " + self._host + ", " + self._name + ": Airpurifier closed the connection.")
            elif re.compile("(.*) ('ping) (.*) (-c 1' returned non-zero exit status 1.)").match(msg):
                self.debug_log(self._host + " offline")
            else:
                self.debug_log(msg)

    def _device_available(self):
        try:
            stdout = self._run("ping " + self._host + " -c 1")

            if stdout:
                if stdout.find('1 packets received') == -1:
                    self._online = False
                    self.debug_log(self._host + " offline")
                else:
                    self._online = True
            else:
                self._online = False
        except Exception as e:
            self.debug_log(self._host + " offline")
            self._online = False

    def _action_send_failed(self, stdout):
        try:
            if stdout is None:
                self.debug_log("command stdout was empty")
                self._inf_loop = 0
                return False
            
            if stdout.find('failed') == -1 or self._inf_loop > 10:
                if self._inf_loop > 10:
                    self.debug_log("inf request resend loop")
                self._inf_loop = 0
                return False
            self._inf_loop = self._inf_loop + 1;
            self.debug_log("request send failed (waiting for resend)")
            time.sleep(0.5)
            return True
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))
            self._inf_loop = 0
            return False
        

    def turn_on(self, speed: str = None, percentage: int = None, preset_mode: str = None, **kwargs: any) -> None:
        if preset_mode is None:
            stdout = self._run(self._cmd + " --pwr 1 --debug")
        else:
            stdout = self.set_preset_mode(preset_mode)

        if self._action_send_failed(stdout):
            self.turn_on(preset_mode)
        else:
            self._update_attributes()

    def turn_off(self, **kwargs) -> None:
        stdout = self._run(self._cmd + " --pwr 0 --debug")

        if self._action_send_failed(stdout):
            self.turn_off()
        else:
            self._update_attributes()

    def set_preset_mode(self, preset_mode: str):
        self.debug_log(preset_mode)
        if self._online == False:
            return ""
        if preset_mode == MODE_OFF:
            stdout = self._run(self._cmd + " --pwr 0 --debug")
        if preset_mode == MANUAL_SPEED_LOW:
            stdout = self._run(self._cmd + " --mode M --om 1 --debug")
        if preset_mode == MANUAL_SPEED_MEDIUM:
            stdout = self._run(self._cmd + " --mode M --om 2 --debug")
        if preset_mode == MANUAL_SPEED_HIGH:
            stdout = self._run(self._cmd + " --mode M --om 3 --debug")
        if preset_mode == MODE_TURBO:
            stdout = self._run(self._cmd + " --mode M --om t --debug")
        if preset_mode == MODE_AUTO:
            stdout = self._run(self._cmd + " --mode P --debug")
        if preset_mode == MODE_ALLERGEN:
            stdout = self._run(self._cmd + " --mode A --debug")
        if preset_mode == MODE_SILENT:
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

    def debug_log(self, error):
        try:
            if self._debug is True:
                _LOGGER.error(error)
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))

    @property
    def preset_mode(self):
        try:
            if self._online == False:
               return None
            if self._attr["mode"] == 'auto':
                return MODE_AUTO
            if self._attr["mode"] == 'allergen':
                return MODE_ALLERGEN
            if self._attr["fan_speed"] == "0":
                return MODE_OFF
            if self._attr["fan_speed"] == "1":
                return MANUAL_SPEED_LOW
            if self._attr["fan_speed"] == "2":
                return MANUAL_SPEED_MEDIUM
            if self._attr["fan_speed"] == "3":
                return MANUAL_SPEED_HIGH
            if self._attr["fan_speed"] == 'turbo':
                return MODE_TURBO
            if self._attr["fan_speed"] == 'silent':
                return MODE_SILENT
            return None
        except Exception as e:
            _LOGGER.error("Unexpected error: {}".format(e))
            return None

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
        return SUPPORT_PRESET_MODE

    @property
    def preset_modes(self):
        return [MODE_OFF, MANUAL_SPEED_LOW, MANUAL_SPEED_MEDIUM, MANUAL_SPEED_HIGH, MODE_TURBO, MODE_ALLERGEN, MODE_AUTO, MODE_SILENT]
