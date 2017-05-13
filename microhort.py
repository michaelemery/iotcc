#!/usr/bin/env python
# --------------------------------------
#
# Massey University
# 158.335
# Creative Design Project 2017
# Microhort (Group 8)
#
# microhort.py
#  Central control module for micro-
#  horticulture project. Generates
#  events based on sensor readings.
#
# Authors:  Michael Emery,
#           Karl Judd,
#           Cliff Whiting.
#
# --------------------------------------


import mysql.connector

cnx = mysql.connector.connect(
    user='iotcc_user',
    password='158335danish',
    host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com',
    database='microhort')
cursor = cnx.cursor()


def main():
    init()


# configure application with all start-up information
def init():
    mac = get_mac('eth0')
    hub = get_hub(mac)
    controllers = get_controllers(hub['hub_id'])
    sensors = get_sensors(hub['hub_id'])
    sensor_limits = get_sensor_limits(hub['hub_id'], hub['hub_profile_id'])
    status(mac, hub, controllers, sensors, sensor_limits)


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
    query = ("SELECT hub_id, hub_name, hub_profile_id, profile_name "
             "FROM hub "
             "JOIN profile "
             "ON hub_profile_id = profile.profile_id "
             "WHERE hub.hub_mac "
             "IN ('{}')".format(mac))
    cursor.execute(query)
    hub = {}
    for hub_id, hub_name, hub_profile_id, profile_name in cursor:
            hub.update({'hub_id': hub_id,
                        'hub_name': hub_name,
                        'hub_profile_id': hub_profile_id,
                        'profile_name': profile_name})
    if not any(hub):
        print("Unregistered MAC (" + mac + ")\nDevice could not be configured.\n")
        exit()
    return hub


# return list of controller info dictionaries for a hub
def get_controllers(hub_id):
    query = ("SELECT hub_controller_id, gpio, hub_controller.controller_type_id, controller_type_name "
             "FROM hub_controller "
             "JOIN controller_type "
             "ON hub_controller.controller_type_id = controller_type.controller_type_id "
             "WHERE hub_controller.hub_id "
             "LIKE ('{}')".format(hub_id))
    cursor.execute(query)
    controllers = []
    for hub_controller_id, gpio, controller_type_id, controller_type_name in cursor:
        controllers.append({'hub_controller_id': hub_controller_id,
                            'gpio': gpio,
                            'controller_type_id': controller_type_id,
                            'controller_type_name': controller_type_name})
    if not any(controllers):
        print("No configured controllers. Add controllers then restart.\n")
        exit()
    return controllers


# return list of sensor info dictionaries for a hub
def get_sensors(hub_id):
    query = ("SELECT hub_sensor_id, gpio, hub_sensor.sensor_type_id, sensor_type_name "
             "FROM hub_sensor "
             "JOIN sensor_type "
             "ON hub_sensor.sensor_type_id = sensor_type.sensor_type_id "
             "WHERE hub_sensor.hub_id "
             "LIKE ('{}')".format(hub_id))
    cursor.execute(query)
    sensors = []
    for hub_sensor_id, gpio, sensor_type_id, sensor_type_name in cursor:
        sensors.append({'hub_sensor_id': hub_sensor_id,
                        'gpio': gpio,
                        'sensor_type_id': sensor_type_id,
                        'sensor_type_name': sensor_type_name})
    if not any(sensors):
        print("No configured sensors. Add sensors then restart.\n")
        exit()
    return sensors


# return profile limits for each configured sensor type
def get_sensor_limits(hub_id, hub_profile_id):
    query = ("SELECT profile_sensor.sensor_type_id, sensor_low, sensor_optimal, sensor_high, sensor_type_name "
             "FROM profile_sensor "
             "JOIN sensor_type "
             "ON profile_sensor.sensor_type_id = sensor_type.sensor_type_id "
             "WHERE profile_sensor.profile_id "
             "LIKE ({})".format(hub_profile_id))
    cursor.execute(query)
    sensor_limits = []
    for sensor_type_id, sensor_low, sensor_optimal, sensor_high, sensor_type_name in cursor:
        sensor_limits.append({'sensor_type_id': sensor_type_id,
                              'sensor_low': sensor_low,
                              'sensor_optimal': sensor_optimal,
                              'sensor_high': sensor_high,
                              'sensor_type_name': sensor_type_name})
    if not any(sensor_limits):
        print("Unable to operate as sensors have no limits.\n")
        exit()
    return sensor_limits


def status(mac, hub, controllers, sensors, sensor_limits):
    print("\nIdentified MAC {}".format(mac))
    print("Welcome to {} running {}.".format(hub['hub_name'], hub['profile_name']))
    print("\nLimits:")
    for sensor_limit in sensor_limits:
        print("  {} ({} -> {} <- {})".format(
            sensor_limit['sensor_type_name'],
            sensor_limit['sensor_low'],
            sensor_limit['sensor_optimal'],
            sensor_limit['sensor_high']))
    print("\nGPIO <-- Sensor Register:")
    for sensor in sensors:
        print("  {:2d} <-- {}".format(sensor['gpio'], sensor['sensor_type_name']))
    print("\nGPIO --> Controller Register:")
    for controller in controllers:
        print("  {:2d} --> {}".format(controller['gpio'], controller['controller_type_name']))
    print("")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cursor.close()
        cnx.close()
