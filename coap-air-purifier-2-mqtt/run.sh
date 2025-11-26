#!/usr/bin/with-contenv bashio
set -euo pipefail

APP_DIR="/usr/src/app"
APP_MAIN="${APP_DIR}/coap-air-purifier-2-mqtt.py"
CONFIG_SRC="/config/coap-air-purifier-2-mqtt/configuration.yaml"
CONFIG_SRC_ALT="/config/coap-air-purifier-2-mqtt/configuration.yml"
CONFIG_PERSIST="/data/configuration.yml"
CONFIG_TARGET="${APP_DIR}/configuration.yml"

bashio::log.info "Preparing configuration"

# Prefer config from /config, fall back to persisted copy in /data
if bashio::fs.file_exists "${CONFIG_SRC}"; then
  bashio::log.info "Using configuration from ${CONFIG_SRC}"
  cp "${CONFIG_SRC}" "${CONFIG_PERSIST}"
elif bashio::fs.file_exists "${CONFIG_SRC_ALT}"; then
  bashio::log.info "Using configuration from ${CONFIG_SRC_ALT}"
  cp "${CONFIG_SRC_ALT}" "${CONFIG_PERSIST}"
elif bashio::fs.file_exists "${CONFIG_PERSIST}"; then
  bashio::log.info "Using existing configuration from ${CONFIG_PERSIST}"
else
  bashio::log.fatal "No configuration file found. Provide ${CONFIG_SRC} (or .yml)."
  exit 1
fi

ln -sf "${CONFIG_PERSIST}" "${CONFIG_TARGET}"

bashio::log.info "Starting Air Purifier CoAP bridge"
cd "${APP_DIR}"
exec python3 "${APP_MAIN}"
