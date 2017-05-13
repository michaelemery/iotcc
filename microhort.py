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
    hub_mac = get_mac('eth0')
    hub_id = get_hub_id(hub_mac)
    print("Hub ID:{}".format(hub_id))
    # hub = get_hub(hub_id)
    # controller = get_hub_controller(hub_id)
    # sensor = get_hub_sensor(hub_id)
    # profile = get_profile()


# return mac address of interface
def get_mac(interface):
    try:
        mac = open('/sys/class/net/' + interface + '/address').read()
    except IOError:
        print("Unknown interface (" + interface + ")\n")
        exit()
    return mac[0:17]


# return hub_id for the given mac address
def get_hub_id(mac):
    query = ("SELECT hub_id, hub_name FROM hub WHERE hub.hub_mac IN ('{}')".format(mac))
    cursor.execute(query)  # TODO guard
    for item_id in cursor:
        pass
    try:
        hub_id = item_id[0]
    except UnboundLocalError:
        print("Unregistered MAC (" + mac + ")\nDevice could not be configured.\n")
        exit()
    return hub_id


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cursor.close()
        cnx.close()
