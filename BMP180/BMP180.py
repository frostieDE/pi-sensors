#!/usr/bin/env python3

import Adafruit_BMP.BMP085 as BMP085
import argparse
import json
import logging
import os
import signal
import sys
import time
import paho.mqtt.client as mqtt

from datetime import datetime

##################################################
# GLOBAL CONFIG
##################################################
caFile = '/ssl/ca_certs.pem'

##################################################
# HANDLE SIGTERM
##################################################
isRunning = True

def handler_stop_signals(signum, frame):
    global isRunning
    logging.getLogger().debug('SIGTERM received')
    logging.getLogger().debug('Shutdown')
    isRunning = False

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

##################################################
# MQTT CALLBACKS
##################################################
isConnected = False;

def on_connected(client, userdata, flags, rc):
    global isConnected
    isConnected = True

def on_disconnected(client, userdata, rc):
    global isConnected
    isConnected = False

##################################################
# CONFIGURATION
##################################################
def config(verbosity, disable_mqtt, test_mode):
    global caFile

    logger = logging.getLogger()

    levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.NOTSET
    }

    if verbosity is not None:
        logging_level = levels.get(verbosity) 
        logging.basicConfig(level=logging_level, format='[%(levelname)s] %(message)s')

    BUS_ADDRESS_ENV = 'BUS_ADDRESS'
    TOPIC_ENV = 'TOPIC'
    MQTT_HOST_ENV = 'MQTT_HOST'
    MQTT_PORT_ENV = 'MQTT_PORT'
    MQTT_USER_ENV = 'MQTT_USER'
    MQTT_PASS_ENV = 'MQTT_PASS'
    MQTT_TLS_ENV = 'MQTT_TLS'
    
    if BUS_ADDRESS_ENV in os.environ:
        address = os.environ[BUS_ADDRESS_ENV]
    else:
        address = 0x77
        logger.info("No I²C address specified. Using I²C address 0x77")

    if TOPIC_ENV in os.environ:
        topic = os.environ[TOPIC_ENV]
    else:
        logger.error('You must specify a MQTT topic');
        quit(1);

    if disable_mqtt is not True:
        if MQTT_HOST_ENV in os.environ:
            mqtt_host = os.environ[MQTT_HOST_ENV]
        else:
            logger.warning("Use default MQTT host: localhost");
            mqtt_host = 'localhost'

        if MQTT_PORT_ENV in os.environ:
            mqtt_port = os.environ[MQTT_PORT_ENV]
        else:
            logger.warning("Use default MQTT port: 1883");
            mqtt_port = 1883

        if MQTT_USER_ENV in os.environ:
            mqtt_user = os.environ[MQTT_USER_ENV]
        else:
            logger.warning("Use default MQTT user: root");
            mqtt_user = 'root'

        if MQTT_PASS_ENV in os.environ:
            mqtt_password = os.environ[MQTT_PASS_ENV]
        else:
            logger.warning("Use default MQTT password: root");
            mqtt_password = 'root'

        if MQTT_TLS_ENV in os.environ and os.environ[MQTT_TLS_ENV] == "True":
            logger.debug("TLS enabled for MQTT")
            mqtt_tls = True

            if MQTT_PORT_ENV not in os.environ:
                mqtt_port = 8883
                logger.warning("Use default MQTT port: 8883 (TLS)")
        else:
            logger.debug("TLS disabled for MQTT")
            mqtt_tls = False

        client = mqtt.Client();

        if mqtt_tls == True:
            logger.debug("Set CA certificated for MQTT client");
            client.tls_set(caFile);

        logger.debug("Enable logger for MQTT client");
        client.enable_logger(logger)

        logger.debug("Set username and password for MQTT client");
        client.username_pw_set(mqtt_user, mqtt_password)

        try:
            logger.debug("Connect to MQTT server")
            client.connect(mqtt_host, mqtt_port)
        except:
            logger.error("Failed to connect to MQTT server");
            quit(2);
    else:
        logger.debug("MQTT client disabled")
        client = None

    if test_mode is True:
        logger.debug("Run in test mode")
        sensor = None
    else:
        sensor = BMP085(address)

    logger.debug("Configuration finished")

    return (logger, topic, sensor, client)

##################################################
# MAIN LOOP
##################################################
def loop(logger, topic, sensor = None, mqtt = None):
    global isRunning

    logger.info('Starting main loop')

    while isRunning:
        logger.debug('Reading sensor')
        if sensor is not None:
            temperature = sensor.readTemperature()
            pressure = sensor.readPressure()
            altitude = sensor.readAltitude()
        else:
            temperature = 24
            pressure = 100700
            altitude = 50.83

        logger.debug("Temperature: %.2f °C" % temperature)
        logger.debug("Pressure: %.2f hPa" % humidity)
        logger.debug("Altitude: %.2f" % altitude)

        json_value = {
                    'temperature': temperature,
                    'pressure': pressure,
                    'altitude': altitude
                }

        logger.debug(json_value)

        if mqtt is not None:
            try:
                if isConnected is not True:
                    logger.info("Reconnecting to MQTT server");
                    mqtt.reconnect()

                mqtt.publish(topic, json.dumps(json_value))
            except:
                logger.error("Publishing to MQTT server failed");

        logger.debug('---');

        time.sleep(2)

    if mqtt is not None:
        logger.debug("Disconnecting from MQTT")
        mqtt.disconnect()

##################################################
# ENTRY POINT
##################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read BMP180 sensor and log to MQTT")
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--disable-mqtt', action='store_true')
    parser.add_argument('--test-mode', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    logger, topic, sensor, client = config(args.verbose, args.disable_mqtt, args.test_mode)
    loop(logger, topic, sensor, client)