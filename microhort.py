#!/usr/bin/env python
# --------------------------------------
#
# microhort.py
#  Central control module for micro-
#  horticulture project. Generates
#  events based on sensor readings.
#
# Massey University
# 158.335
# Creative Design Project 2017
# Microhort (Group 8)
#
# Authors:  Michael Emery,
#           Karl Judd,
#           Cliff Whiting.
#
# --------------------------------------


import os
import RPi.GPIO as GPIO
import mysql.connector
import Adafruit_DHT
import json
import time
import copy
import data_log_request
from time import strftime
from datetime import datetime
from picamera import PiCamera
import requests


# --- SET GLOBAL CONSTANTS ---
SERVER = "http://ec2-54-70-146-220.us-west-2.compute.amazonaws.com"
# TODO - replace this with microhort.com
# # connection
# CONN = mysql.connector.connect(
#     user='iotcc_user',
#     password='158335danish',
#     host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com',
#     database='microhort')
# CURSOR = CONN.cursor()

# hardware info
HT_SENSOR_MODEL = Adafruit_DHT.DHT22
CAMERA = PiCamera()
CAMERA.vflip = True
CAMERA.hflip = True

# set GPIO constants
GPIO_OFF = GPIO.LOW
GPIO_ON  = GPIO.HIGH
CONFIG_SWITCH = 26
CAMERA_SWITCH = 19
CONFIG_LED = 21
GPIO_INPUT = [17, 27, 22, 5, 6, 13]
GPIO_OUTPUT = [18, 23, 24, 25, 12, 16, 20, 21]

# configure GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(CONFIG_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CAMERA_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_INPUT, GPIO.IN)
GPIO.setup(GPIO_OUTPUT, GPIO.OUT)
GPIO.add_event_detect(CONFIG_SWITCH, GPIO.FALLING)
GPIO.add_event_detect(CAMERA_SWITCH, GPIO.FALLING)

# set profile state constants
LOW = -1
STABLE = 0
HIGH = 1

# set lighting constants
LIGHTING_ON = True
LIGHTING_OFF = False

# set file constants
JSON_FILE = '/home/' + os.environ['SUDO_USER'] + '/microhort/microhort.json'
IMAGE_PATH = '/home/' + os.environ['SUDO_USER'] + '/microhort/image/'

# set daily image capture-time constant
CAPTURE_TIME = '12:00'


def main():
    while True:
        config = init()
        previous_capture_date = '1970-01-01'
        GPIO.output(CONFIG_LED, GPIO_ON)
        lighting_state = LIGHTING_OFF
        switch_lights(lighting_state, config['lighting_gpio'], 'SYSTEM START')
        previous_sensor_type_states = init_sensor_type_states(config['sensor'])
        while not GPIO.event_detected(CONFIG_SWITCH):
            sensor_type_states = evaluate_sensor_type_states(
                copy.deepcopy(previous_sensor_type_states), config['sensor'], config['profile_sensor']
            )
            for sensor_type_id in sensor_type_states:
                if sensor_type_states[sensor_type_id] != previous_sensor_type_states[sensor_type_id]:
                    previous_sensor_type_states[sensor_type_id] = init_sensor_type_states(config['sensor'])
                    signal_event(sensor_type_states, sensor_type_id, config)
            previous_sensor_type_states = sensor_type_states
            lighting_state = set_profile_lighting(config['lighting_gpio'], config['profile'], lighting_state)
            current_time = strftime('%H:%M')
            current_date = strftime('%Y-%m-%d')
            if current_time == CAPTURE_TIME and current_date > previous_capture_date:
                capture_image(IMAGE_PATH, 'AUTO', current_time)
                previous_capture_date = current_date
            if GPIO.event_detected(CAMERA_SWITCH):
                capture_image(IMAGE_PATH, 'MANUAL', current_time)

        flush_event(CONFIG_SWITCH)
        print('\n\n======= SYSTEM RESTARTED =======\n')


# configure application with all start-up information
# def init():
#     hub = get_hub(get_mac('eth0'))
#     config = {
#         'hub': hub,
#         'controller_type': get_controller_types(),
#         'controller': get_controllers(hub['hub_id']),
#         'sensor_type': get_sensor_types(),
#         'sensor': get_sensors(hub['hub_id']),
#         'profile': get_profile(hub['hub_profile_id']),
#         'profile_sensor': get_profile_sensor(hub['hub_profile_id']),
#         'lighting_gpio': get_lighting(hub['hub_profile_id'])
#     }
#     show_config(config)
#     write_config(config, JSON_FILE)
#     print("\nRunning (ctrl-c to abort)\n")
#     return config


# configure application with all start-up information
def init():
    mac = get_mac('eth0')
    # send HTTP GET to retrieve hub information	
    url = SERVER + "/getconfig"
    params = {"mac":str(mac)}
    resp = requests.get(url=url, params=params)
    print(resp)
    config = convertMicroHortDictionary(json.loads(resp.text))
    show_config(config)
    write_config(config, JSON_FILE)
    print("\nRunning (ctrl-c to abort)\n")
    return config


# build list of unique sensor types and initialise them with state of OPTIMAL
def init_sensor_type_states(sensors):
    sensor_type_states = {}
    for sensor in sensors:
        if sensor['sensor_type_id'] not in sensor_type_states:
            sensor_type_states[sensor['sensor_type_id']] = STABLE
    return sensor_type_states


# returns the state (LOW, OPTIMAL, HIGH) of all sensor types
def evaluate_sensor_type_states(sensor_type_states, sensors, profile):
    for sensor_type_id in sensor_type_states:
        average = get_average_value(sensor_type_id, sensors)
        if profile[sensor_type_id]['profile_sensor_low'] is not None and \
                average <= profile[sensor_type_id]['profile_sensor_low']:
            sensor_type_states[sensor_type_id] = LOW
        elif profile[sensor_type_id]['profile_sensor_high'] is not None and \
                average >= profile[sensor_type_id]['profile_sensor_high']:
            sensor_type_states[sensor_type_id] = HIGH
        else:
            sensor_type_states[sensor_type_id] = STABLE
    return sensor_type_states


# returns the average sensor reading for the specified sensor type
def get_average_value(sensor_type_id, sensors):
    total = 0
    count = 0
    for sensor in sensors:
        if sensor['sensor_type_id'] == sensor_type_id:
            if sensor['sensor_type_id'] == 1:
                humidity, temperature = Adafruit_DHT.read_retry(HT_SENSOR_MODEL, sensor['sensor_gpio'])
                total += temperature
                count += 1
                print('Temperature: {}'.format(int(total / count)))
            if sensor['sensor_type_id'] == 2:
                humidity, temperature = Adafruit_DHT.read_retry(HT_SENSOR_MODEL, sensor['sensor_gpio'])
                total += humidity
                count += 1
                print('   Humidity: {}'.format(int(total / count)))
        time.sleep(2)
    return int(total / count)


# generates an event log and signals an event to be controlled
def signal_event(sensor_type_state, sensor_type_id, config):
    state_dictionary = {-1: 'Low', -0: 'Stable', 1: 'High'}
    event_message = "{}: {} {} {}".format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        config['hub']['hub_name'],
        config['sensor_type'][sensor_type_id]['sensor_type_name'],
        state_dictionary[sensor_type_state[sensor_type_id]]
    )
    print("\n[SENSOR] {}\n".format(event_message))
    event_entry = {
        'event_dtg:': str(datetime.now()),
        'event_hub_id': config['hub']['hub_id'],
        'event_profile_id': config['hub']['hub_profile_id'],
        'event_sensor_type_id': sensor_type_id,
        'event_state': sensor_type_state[sensor_type_id],
        'event_message': event_message
    }
    append_event(event_entry)
    action_controller(event_entry, config['controller_type'], config['controller'], config['sensor_type'])


# toggles lighting as required for profile and returns state of profile lighting
def set_profile_lighting(lighting_gpio, lighting_profile, lighting_state):
    current_time = strftime('%H:%M')
    time_on = lighting_profile['profile_lighting_on']
    time_off = lighting_profile['profile_lighting_off']
    if time_on <= current_time < time_off and lighting_state == LIGHTING_OFF:
        switch_lights(LIGHTING_ON, lighting_gpio, current_time)
        lighting_state = LIGHTING_ON
    elif time_off <= current_time and lighting_state == LIGHTING_ON:
        switch_lights(LIGHTING_OFF, lighting_gpio, current_time)
        lighting_state = LIGHTING_OFF
    return lighting_state


# switch lights on or off
def switch_lights(lights_are_on, lighting_gpio, message):
    if lights_are_on:
        state = GPIO_ON
        text = 'ON'
    else:
        state = GPIO_OFF
        text = 'OFF'
    GPIO.output(lighting_gpio, state)
    print("\n[LIGHTS] ### " + text + " : {}\n".format(message))


# writes an entry in the event log
def append_event(event_entry):
    data_log_request.http_request(event_entry)
    pass


# stabilises the profile when in a non-stable event state
def action_controller(event_entry, controller_type, controller, sensor_type):
    sensor_type_id = event_entry['event_sensor_type_id']
    event_state = event_entry['event_state']
    # controller_type_id = controller_type['controller_type_id']
    if event_state is HIGH:
        controller = sensor_type[sensor_type_id]['sensor_type_high_controller_type_id']
    elif event_state is LOW:
        controller = sensor_type[sensor_type_id]['sensor_type_low_controller_type_id']
    elif event_state is STABLE:
        # turn everything off
        pass


# return mac address of interface
def get_mac(interface):
    try:
        mac = open('/sys/class/net/' + interface + '/address').read()
    except IOError:
        print("Unknown interface (" + interface + ")\n")
        exit()
    return mac[0:17]


# return hub info dictionary matching a mac address
def get_hub(mac):
    query = (
        "SELECT hub_id, hub_mac, hub_name, hub_profile_id "
        "FROM hub "
        "WHERE hub_mac "
        "LIKE ('{}')".format(mac)
    )
    CURSOR.execute(query)
    hub = {}
    for hub_id, hub_mac, hub_name, hub_profile_id in CURSOR:
        hub.update({
            'hub_id': hub_id,
            'hub_mac': hub_mac,
            'hub_name': hub_name,
            'hub_profile_id': hub_profile_id})
    if not any(hub):
        print("Unregistered MAC (" + mac + ")\nDevice could not be configured.\n")
        exit()
    return hub


# returns a dictionary of controller types indexed by type id
def get_controller_types():
    query = (
        "SELECT controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time  "
        "FROM controller_type "
    )
    CURSOR.execute(query)
    controller_types = {}
    for controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time in CURSOR:
        controller_types.update({controller_type_id: {
            'controller_type_name': controller_type_name,
            'controller_type_max_run_time': controller_type_max_run_time,
            'controller_type_min_rest_time': controller_type_min_rest_time}})
    return controller_types


# returns a list of dictionaries for each controller
def get_controllers(hub_id):
    query = (
        "SELECT controller_id, controller_gpio, controller_type_id  "
        "FROM controller "
        "WHERE controller_hub_id "
        "LIKE ('{}')".format(hub_id)
    )
    CURSOR.execute(query)
    controller = []
    for controller_id, controller_gpio, controller_type_id in CURSOR:
        controller.append({
            'controller_id': controller_id,
            'controller_gpio': controller_gpio,
            'controller_type_id': controller_type_id})
    if not any(controller):
        print("No configured controllers. Add controllers then restart.\n")
        exit()
    return controller


# returns a dictionary of sensor types indexed by type id
def get_sensor_types():
    query = (
        "SELECT sensor_type_id, sensor_type_name, sensor_type_low_controller_type_id, "
        "sensor_type_high_controller_type_id "
        "FROM sensor_type "
    )
    CURSOR.execute(query)
    sensor_types = {}
    for sensor_type_id, sensor_type_name, sensor_type_low_controller_type_id, sensor_type_high_controller_type_id \
            in CURSOR:
        sensor_types.update({sensor_type_id: {
            'sensor_type_name': sensor_type_name,
            'sensor_type_low_controller_type_id': sensor_type_low_controller_type_id,
            'sensor_type_high_controller_type_id': sensor_type_high_controller_type_id}})
    return sensor_types


# returns a list of dictionaries for each sensor
def get_sensors(hub_id):
    query = (
        "SELECT sensor_id, sensor_gpio, sensor_type_id "
        "FROM sensor "
        "WHERE sensor_hub_id "
        "LIKE ('{}')".format(hub_id)
    )
    CURSOR.execute(query)
    sensor = []
    for sensor_id, sensor_gpio, sensor_type_id in CURSOR:
        sensor.append({
            'sensor_id': sensor_id,
            'sensor_gpio': sensor_gpio,
            'sensor_type_id': sensor_type_id})
    if not any(sensor):
        print("No configured sensors. Add sensors then restart.\n")
        exit()
    return sensor


# return profile information for given profile id
def get_profile(hub_profile_id):
    query = (
        "SELECT profile_id, profile_name, profile_lighting_on, profile_lighting_off "
        "FROM profile "
        "WHERE profile.profile_id "
        "LIKE ({})".format(hub_profile_id)
    )
    CURSOR.execute(query)
    profile = {}
    for profile_id, profile_name, profile_lighting_on, profile_lighting_off in CURSOR:
        profile = {
            'profile_id': profile_id,
            'profile_name': profile_name,
            'profile_lighting_on': profile_lighting_on,
            'profile_lighting_off': profile_lighting_off}
    return profile


# return sensor profiles for given hub profile
def get_profile_sensor(hub_profile_id):
    query = (
        "SELECT profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_high "
        "FROM profile_sensor "
        "WHERE profile_id "
        "LIKE ({})".format(str(hub_profile_id))
    )
    CURSOR.execute(query)
    profile_sensor = {}
    for profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_high in CURSOR:
        profile_sensor.update({
            sensor_type_id: {
                'profile_sensor_low': profile_sensor_low,
                'profile_sensor_high': profile_sensor_high
            }
        })
    return profile_sensor


# return lighting ports
def get_lighting(hub_profile_id):
    query = (
        "SELECT lighting_id, lighting_hub_id, lighting_gpio "
        "FROM lighting "
        "WHERE lighting_hub_id "
        "LIKE %s"
    )
    CURSOR.execute(query, str(hub_profile_id))
    lighting = []
    for lighting_id, lighting_hub_id, lighting_gpio in CURSOR:
        lighting.append(lighting_gpio)
    return lighting


# output configuration summary to the console
def show_config(config):
    print("\nIdentified MAC {}".format(config['hub']['hub_mac']))
    print("Welcome to {} running {}.".format(config['hub']['hub_name'], config['profile']['profile_name']))
    print("\nLimits:")
    for sensor_type in config['sensor_type']:
        print("  {} ({} <-> {})".format(
            config['sensor_type'][sensor_type]['sensor_type_name'],
            config['profile_sensor'][sensor_type]['profile_sensor_low'],
            config['profile_sensor'][sensor_type]['profile_sensor_high']))
    print("  Lights ON from {} to {}.".format(
        config['profile']['profile_lighting_on'],
        config['profile']['profile_lighting_off']
    ))

    print("\nGPIO <-- Sensor Register:")
    for sensor_type in config['sensor']:
        print("  {:2d} <-- {}".format(sensor_type['sensor_gpio'],
                                      config['sensor_type'][sensor_type['sensor_type_id']]['sensor_type_name']));
    print("\nGPIO --> Controller Register:")
    for controller in config['controller']:
        print("  {:2d} --> {}".format(controller['controller_gpio'],
                                      config['controller_type'][controller['controller_type_id']][
                                          'controller_type_name']))
    print("\nGPIO --> Lighting Register:")
    for lighting in config['lighting_gpio']:
        print("  {:2d} --> Lighting Array".format(lighting))
    print("")


# capture image from camera and save to file
def capture_image(path, tag, timestamp):
    filename = strftime('%Y%m%d-%H%M-%S') + ".jpg"
    CAMERA.capture("{}{}-{}".format(path, tag, filename))
    print("\n[CAMERA] ### {} {}: {}\n".format(tag, timestamp, filename))
    flush_event(CAMERA_SWITCH)


# write configuration data to file
def write_config(config, filename):
    with open(filename, 'w') as f:
        json.dump(config, f)


# read configuration data from file
def read_config(filename):
    with open(filename, 'r') as f:
        config = ConvertMicroHortDictionary(json.load(f))
    return config


# flush residual button presses to prevent false events
def flush_event(gpio):
    time.sleep(0.5)
    GPIO.event_detected(gpio)


# Convert the JSON to work a PY dict with int keys.
# This makes any keys that are int+strings become ints.
# if something is broken loading from read_config(), it could definitely be this code.
def convertIfDigit(dictionary):
    for k in dictionary:
        if (type(k) is str or type(k) is unicode) and k.isdigit():
            dictionary[int(k)] = dictionary.pop(k)
    return dictionary

def convertMicroHortDictionary(dictionary):
    if type(dictionary) is not dict:
        return
    for k in dictionary:
        if type(dictionary[k]) is dict:
            convertIfDigit(dictionary[k])
            convertMicroHortDictionary(dictionary[k])
    return dictionary


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
