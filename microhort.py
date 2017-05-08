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

# set operating constants
LOW     = -1
OPTIMAL = 0
HIGH    = 1

cnx = mysql.connector.connect(user='iotcc_user', password='158335danish', host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com', database='microhort')
cursor = cnx.cursor()


def main():
    initialise()


def initialise():
    query = ("SELECT owner_id, owner_nickname, owner_email FROM owner ")
    cursor.execute(query)
    for (owner_id, owner_nickname, owner_email) in cursor:
        print("{}. {} ({}).".format(owner_id, owner_nickname, owner_email))
    cursor.close()
    cnx.close()


def read():
    return


def evaluate(sensor_type_id, mean_value):
    return


def action(sensor_type_id, mean_value, target_value):
    return


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cursor.close()
        cnx.close()