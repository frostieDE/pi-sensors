#!/usr/bin/env python3

import Adafruit_DHT
import argparse
import logging
import os
import signal
import sys
import time

from influxdb import InfluxDBClient
from datetime import datetime

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
def config(verbosity, disable_influx):
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
    INFLUX_HOST_ENV = 'INFLUX_HOST'
    INFLUX_PORT_ENV = 'INFLUX_PORT'
    INFLUX_USER_ENV = 'INFLUX_USER'
    INFLUX_PASS_ENV = 'INFLUX_PASS'
    INFLUX_DB_ENV = 'INFLUX_DB'
    
    if PIN_ENV in os.environ:
        pin = os.environ[PIN_ENV]
    else:
        logger.error('You must specify DHT22_PIN environment variable')
        quit(1)

    if disable_influx is not True:

        if INFLUX_HOST_ENV in os.environ:
            influx_host = os.environ[INFLUX_HOST_ENV]
        else:
            logger.warning("Use default influx host: localhost");
            influx_host = 'localhost'

        if INFLUX_PORT_ENV in os.environ:
            influx_port = os.environ[INFLUX_PORT_ENV]
        else:
            logger.warning("Use default influx port: 8086");
            influx_port = 8086

        if INFLUX_USER_ENV in os.environ:
            influx_user = os.environ[INFLUX_USER_ENV]
        else:
            logger.warning("Use default influx user: root");
            influx_user = 'root'

        if INFLUX_PASS_ENV in os.environ:
            influx_password = os.environ[INFLUX_PASS_ENV]
        else:
            logger.warning("Use default influx password: root");
            influx_password = 'root'

        if INFLUX_DB_ENV in os.environ:
            influx_db = os.environ[INFLUX_DB_ENV]
        else:
            logger.error('You must specify INFLUX_DB_ENV environment variable')
            quit(1)

        client = InfluxDBClient(influx_host, influx_port, influx_user, influx_password, influx_db)
    else:
        client = None

    sensor = Adafruit_DHT.DHT22

    return (logger, sensor, pin, client)

##################################################
# MAIN LOOP
##################################################
def loop(logger, sensor, pin, client = None):
    global isRunning

    logger.info('Starting main loop')

    while isRunning:
        logger.info('Reading sensor')
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin);
        logger.info("Temperature: %s" % temperature)
        logger.info("Humidity: %s" % humidity)
        logger.info('---');

        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        json_body = [
            {
                "measurement": "temperature",
                "tags": {
                    "room": "Room One"    
                },
                "time": current_time,
                "fields": {
                    "value": temperature    
                }
            },
            {
                "measurement": "humidity",
                "tags": {
                    "room": "Room One"    
                },
                "time": current_time,
                "fields": {
                    "value": humidity
                }
            }
        ]
        logger.debug(json_body)

        if client is not None:
            logger.info('Log to InfluxDB')
            client.write_points(json_body)

        time.sleep(2)

##################################################
# ENTRY POINT
##################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read DHT22 sensor and log to InfluxDB")
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--disable-influx', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    logger, sensor, pin, client = config(args.verbose, args.disable_influx)
    loop(logger, sensor, pin, client)