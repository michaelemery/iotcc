#!/usr/bin/env python
# --------------------------------------
#
# sense_thp.py
#
# Author: Michael Emery (12154337)
#         158.335 Lab 3
#
# --------------------------------------

from sense_hat import SenseHat

sense = SenseHat()
sense.clear()

temperature = sense.get_temperature()
humidity = sense.get_humidity()
pressure = sense.get_pressure()
print("Temperature : {}".format(temperature))
print("Humidity    : {}".format(humidity))
print("Pressure    : {}".format(pressure))

