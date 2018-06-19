#!/usr/bin/env python3

import Adafruit_DHT
import argparse
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
# CONFIGURATION
##################################################
def config(verbosity, disable_influx, test_mode):
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

    PIN_ENV = 'DHT22_PIN'
    TOPIC_ENV = 'TOPIC'
    MQTT_HOST_ENV = 'MQTT_HOST'
    MQTT_PORT_ENV = 'MQTT_PORT'
    MQTT_USER_ENV = 'MQTT_USER'
    MQTT_PASS_ENV = 'MQTT_PASS'
    MQTT_TLS_ENV = 'MQTT_TLS'
    
    if PIN_ENV in os.environ:
        pin = os.environ[PIN_ENV]
    else:
        logger.error('You must specify DHT22_PIN environment variable')
        quit(1)

    if TOPIC_ENV in os.environ:
        topic = os.environ[TOPIC_ENV]
    else:
        logger.error('You must specify a MQTT topic');
        quit(1);

    if disable_influx is not True:

        if MQTT_HOST_ENV in os.environ:
            mqtt_host = os.environ[MQTT_HOST_ENV]
        else:
            logger.warning("Use default influx host: localhost");
            mqtt_host = 'localhost'

        if MQTT_PORT_ENV in os.environ:
            mqtt_port = os.environ[MQTT_PORT_ENV]
        else:
            logger.warning("Use default influx port: 8086");
            mqtt_port = 8086

        if MQTT_USER_ENV in os.environ:
            mqtt_user = os.environ[MQTT_USER_ENV]
        else:
            logger.warning("Use default influx user: root");
            mqtt_user = 'root'

        if MQTT_PASS_ENV in os.environ:
            mqtt_password = os.environ[MQTT_PASS_ENV]
        else:
            logger.warning("Use default influx password: root");
            mqtt_password = 'root'

        if MQTT_TLS_ENV in os.environ and os.environ[MQTT_TLS_ENV] == "True":
            mqtt_tls = True
        else:
            mqtt_tls = False

        client = mqtt.Client();

        if mqtt_tls == True:
            client.tls_set(caFile);

        client.enable_logger(logger)
        client.username_pw_set(mqtt_user, mqtt_password)

        try:
            client.connect(mqtt_host, mqtt_port)
        except:
            logger.error("Failed to connect to MQTT server");
            quit(2);
    else:
        client = None

    if test_mode is True:
        sensor = None
    else:
        sensor = Adafruit_DHT.DHT22

    return (logger, topic, pin, sensor, client)

##################################################
# MAIN LOOP
##################################################
def loop(logger, topic, pin, sensor = None, mqtt = None):
    global isRunning

    logger.info('Starting main loop')

    while isRunning:
        logger.debug('Reading sensor')
        if sensor is not None:
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin);
        else:
            humidity = 48.5
            temperature = 24

        logger.debug("Temperature: %s" % temperature)
        logger.debug("Humidity: %s" % humidity)

        if mqtt is not None:
            try:
                mqtt.publish(topic + "/temperature", temperature)
                mqtt.publish(topic + "/humidity", humidity)
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
    parser = argparse.ArgumentParser(description="Read DHT22 sensor and log to InfluxDB")
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--disable-mqtt', action='store_true')
    parser.add_argument('--test-mode', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    logger, topic, pin, sensor, client = config(args.verbose, args.disable_mqtt, args.test_mode)
    loop(logger, topic, pin, sensor, client)