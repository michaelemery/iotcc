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


# TODO LIST
# add connector to RPi
# point to remote MySQL server

import mysql.connector

cnx = mysql.connector.connect(user='iotcc_user', password='158335danish', host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com', database='microhort')
cursor = cnx.cursor()


def main():
    view_controller_type()
    view_owner()
    view_environment()
    view_environment_sensor()
    view_sensor_type()
    print("")
    cursor.close()
    cnx.close()


def view_controller_type():
    heading("Controller Type")
    query = ("SELECT controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time "
             "FROM controller_type")
    cursor.execute(query)
    for (controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time) \
            in cursor:
        print("{0:6d} {1:20s} {2:6d} {3:6d}".format(controller_type_id, controller_type_name,
                                                    controller_type_max_run_time, controller_type_min_rest_time))


def view_owner():
    heading("Owner")
    query = ("SELECT owner_id, owner_nickname, owner_email "
             "FROM owner")
    cursor.execute(query)
    for (owner_id, owner_nickname, owner_email) in cursor:
        print("{0:6d} {1:20} {2}".format(owner_id, owner_nickname, owner_email))


def view_environment():
    heading("Environment")
    query = ("SELECT environment_id, environment_name "
             "FROM environment")
    cursor.execute(query)
    for (environment_id, environment_name) in cursor:
        print("{0:6d} {1:20}".format(environment_id, environment_name))


def view_environment_sensor():
    heading("Environment Sensors")
    query = ("SELECT environment_sensor.environment_sensor_id, environment_name, sensor_type_name, sensor_low, sensor_optimal, sensor_high "
             "FROM environment_sensor "
             "JOIN environment ON environment_sensor.environment_id=environment.environment_id "
             "JOIN sensor_type ON environment_sensor.sensor_id=sensor_type.sensor_type_id")
    cursor.execute(query)
    for (environment_sensor_id, environment_name, sensor_type_name, sensor_low, sensor_optimal, sensor_high) in cursor:
        print("{0:6d} {1:20} {2:10} {3:6} {4:6} {5:6}".format(environment_sensor_id, environment_name, sensor_type_name, sensor_low, sensor_optimal, sensor_high))


def view_sensor_type():
    heading("Sensors")
    query = ("SELECT sensor_type_id, sensor_type_name "
             "FROM sensor_type")
    cursor.execute(query)
    for (sensor_type_id, sensor_type_name) in cursor:
        print("{0:6d} {1:20}".format(sensor_type_id, sensor_type_name))


def heading(heading):
    print("\n" + heading)
    print('-' * len(heading))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cursor.close()
        cnx.close()
