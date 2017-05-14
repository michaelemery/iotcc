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

import mysql.connector
import json

# --- SET GLOBAL CONSTANTS ---

# connection
CONN = mysql.connector.connect(
    user='iotcc_user',
    password='158335danish',
    host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com',
    database='microhort')
CURSOR = CONN.cursor()

# state
LOW = -1
OPTIMAL = 0
HIGH = 1


def main():
    config = init()
    show_config(config)
    write_config(config, 'microhort.json')
    sensor_state = init_sensor_states(config)
    while True:
        previous_sensor_state = sensor_state
        sensor_state = evaluate_state(previous_sensor_state)
        print(sensor_state)
        exit()


def evaluate_state(previous_sensor_state):
    #for sensor_type in previous_sensor_state:
        #get_average_value(sensor_type)
    return None


def init_sensor_states(config):
    sensor_state = {}
    for sensor in config['sensor']:
        if sensor['sensor_type_id'] not in sensor_state:
            sensor_state.update({sensor['sensor_type_id']: OPTIMAL})
    return sensor_state


# configure application with all start-up information
def init():
    hub = get_hub(get_mac('eth0'))
    config = {
        'hub': hub,
        'controller_type': get_controller_types(),
        'controller': get_controllers(hub['hub_id']),
        'sensor_type': get_sensor_types(),
        'sensor': get_sensors(hub['hub_id']),
        'profile': get_profile(hub['hub_profile_id']),
        'profile_sensor': get_profile_sensor(hub['hub_profile_id'])}
    return config


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


def get_controllers(hub_id):
    query = (
        "SELECT controller_id, controller_gpio, controller_type_id  "
        "FROM controller "
        "WHERE controller.hub_id "
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


# return list of sensor info dictionaries for a hub
def get_sensors(hub_id):
    query = (
        "SELECT sensor_id, sensor_gpio, sensor_type_id "
        "FROM sensor "
        "WHERE sensor.hub_id "
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
        "SELECT profile_id, profile_name "
        "FROM profile "
        "WHERE profile.profile_id "
        "LIKE ({})".format(hub_profile_id)
    )
    CURSOR.execute(query)
    profile = {}
    for profile_id, profile_name in CURSOR:
        profile = {'profile_id': profile_id, 'profile_name': profile_name}
    return profile


# return sensor profiles for given hub profile
def get_profile_sensor(hub_profile_id):
    query = (
        "SELECT profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_optimal, "
        "profile_sensor_high "
        "FROM profile_sensor "
        "WHERE profile_id "
        "LIKE %s"
    )
    CURSOR.execute(query, str(hub_profile_id))
    profile_sensor = []
    for profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_optimal, profile_sensor_high in CURSOR:
        profile_sensor.append({
            'profile_sensor_id': profile_sensor_id,
            'profile_id': profile_id,
            'sensor_type_id': sensor_type_id,
            'profile_sensor_low': profile_sensor_low,
            'profile_sensor_optimal': profile_sensor_optimal,
            'profile_sensor_high': profile_sensor_high
        })
    return profile_sensor


# output configuration summary to the console
def show_config(config):
    print("\nIdentified MAC {}".format(config['hub']['hub_mac']))
    print("Welcome to {} running {}.".format(config['hub']['hub_name'], config['profile']['profile_name']))
    print("\nLimits:")
    for sensor in config['profile_sensor']:
        print("  {} ({} -> {} <- {})".format(config['sensor_type'][sensor['sensor_type_id']]['sensor_type_name'],
                                             sensor['profile_sensor_low'],
                                             sensor['profile_sensor_optimal'],
                                             sensor['profile_sensor_high']))
    print("\nGPIO <-- Sensor Register:")
    for sensor in config['sensor']:
        print("  {:2d} <-- {}".format(sensor['sensor_gpio'], config['sensor_type'][sensor['sensor_type_id']]['sensor_type_name']));
    print("\nGPIO --> Controller Register:")
    for controller in config['controller']:
        print("  {:2d} --> {}".format(controller['controller_gpio'],
                                      config['controller_type'][controller['controller_type_id']]['controller_type_name']))
    print("")


# write configuration data to file
def write_config(config, filename):
    with open(filename, 'w') as f:
        json.dump(config, f)


# read configuration data from file
def read_config(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        CURSOR.close()
        CONN.close()
