#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response
import mysql.connector
import json

# TODO - make sure to remove sensitive info from Exceptions & turn debug mode off!

app = Flask(__name__)

def getDbCursor():
    connection = mysql.connector.connect(user='iotcc_user',password='158335danish',host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com',database='microhort')
    cursor = connection.cursor()
    return connection, cursor
    
def cleanUpDb(connection, cursor):
    cursor.close()
    connection.close()
    
    
@app.route('/')
def homepage():
    return '158335 MicroHort project'


@app.route('/hello')
def hello():
    return 'Hello 2, i hope i am working.'


@app.route('/testjsonresponse')
def testJsonResponse():
    if request.method == 'GET':
        test = {'name': 'bob', 'age': '20', 'height': '180cm'}
        return jsonify(**test)
    else:
        return 'Method not recognized'


@app.route('/testjsonresponse2')
def testJsonResponse2():
    if request.method == 'GET':
        test = {'name': 'bob', 'age': '20', 'height': '180cm'}
        return jsonify(**test)
    else:
        return 'Method not recognized'
        
@app.route('/querydb')
def querydb():
    connection, cursor = getDbCursor()
    args = request.args.to_dict()
    q= args["query"]
    cursor.execute(q)
    r = list(cursor)
    result_str = ""
    for result in r:
        result_str += str(result)
    return result_str


@app.route('/testdb')
def testDb():
    mac = "b8:27:eb:bc:4d:a4"
    connection, cursor = getDbCursor()
    query = (
        "SELECT hub_id, hub_mac, hub_name, hub_profile_id "
        "FROM hub "
        "WHERE hub_mac "
        "LIKE ('{}')".format(mac)
    )
    cursor.execute(query)
    hub = {}
    for hub_id, hub_mac, hub_name, hub_profile_id in cursor:
        hub.update({
            'hub_id': hub_id,
            'hub_mac': hub_mac,
            'hub_name': hub_name,
            'hub_profile_id': hub_profile_id})
    if not any(hub):
        hub = {"failed":"1"}
        print("Unregistered MAC (" + mac + ")\nDevice could not be configured.\n")
    cleanUpDb(connection,cursor)
    return jsonify(**hub)


@app.route('/gethub')
def getHub():
    #retrieve arguments
    args = request.args.to_dict()
    # currently only want the mac adr, could add in more params in future.
    mac = args["mac"]
    #query database to retrive hub information
    connection, cursor = getDbCursor()
    query = (
        "SELECT hub_id, hub_mac, hub_name, hub_profile_id "
        "FROM hub "
        "WHERE hub_mac "
        "LIKE ('{}')".format(mac)
    )
    cursor.execute(query)
    hub = {}
    for hub_id, hub_mac, hub_name, hub_profile_id in cursor:
        hub.update({
            'hub_id': hub_id,
            'hub_mac': hub_mac,
            'hub_name': hub_name,
            'hub_profile_id': hub_profile_id})
    if not any(hub):
        hub = {"failed":"1"}
# 		print("Unregistered MAC (" + mac + ")\nDevice could not be configured.\n")
    cleanUpDb(connection,cursor)
    return json.dumps(hub)
    # return jsonify(**hub) #returns a JSON object of the hub request. Should NOT contain unicode chars.

@app.route('/getcontrollertypes')
def getControllerTypes():
    connection, cursor = getDbCursor()
    query = (
        "SELECT controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time  "
        "FROM controller_type "
        )
    cursor.execute(query)
    controller_types = {}
    for controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time in cursor:
        controller_types.update({controller_type_id: {
        'controller_type_name': controller_type_name,
        'controller_type_max_run_time': controller_type_max_run_time,
        'controller_type_min_rest_time': controller_type_min_rest_time}})
    cleanUpDb(connection,cursor)
    print(controller_types)
    return json.dumps(controller_types)

@app.route('/getconfig')
def getconfig():
    #get arguments
    args = request.args.to_dict()
    #get hub
    mac = args["mac"]
    connection, cursor = getDbCursor()
    hub = get_hub(mac, cursor)
    config = {
        'hub': hub,
        'controller_type': get_controller_types(cursor),
        'controller': get_controllers(hub['hub_id'], cursor),
        'sensor_type': get_sensor_types(cursor),
        'sensor': get_sensors(hub['hub_id'], cursor),
        'profile': get_profile(hub['hub_profile_id'], cursor),
        'profile_sensor': get_profile_sensor(hub['hub_profile_id'], cursor)}
    #return the config as a JSON object
    return json.dumps(config)
    
def get_hub(mac,cursor):
    query = (
        "SELECT hub_id, hub_mac, hub_name, hub_profile_id "
        "FROM hub "
        "WHERE hub_mac "
        "LIKE ('{}')".format(mac)
        )
    cursor.execute(query)
    hub = {}
    for hub_id, hub_mac, hub_name, hub_profile_id in cursor:
        hub.update({
            'hub_id': hub_id,
            'hub_mac': hub_mac,
            'hub_name': hub_name,
            'hub_profile_id': hub_profile_id})
    return hub

def get_controller_types(cursor):
    query = (
        "SELECT controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time  "
        "FROM controller_type "
    )
    cursor.execute(query)
    controller_types = {}
    for controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time in cursor:
        controller_types.update({controller_type_id: {
            'controller_type_name': controller_type_name,
            'controller_type_max_run_time': controller_type_max_run_time,
            'controller_type_min_rest_time': controller_type_min_rest_time}})
    return controller_types

def get_controllers(hub_id, cursor):
    query = (
        "SELECT controller_id, controller_gpio, controller_type_id  "
        "FROM controller "
        "WHERE controller.hub_id "
        "LIKE ('{}')".format(hub_id)
    )
    cursor.execute(query)
    controller = []
    for controller_id, controller_gpio, controller_type_id in cursor:
        controller.append({
            'controller_id': controller_id,
            'controller_gpio': controller_gpio,
            'controller_type_id': controller_type_id})
    return controller
    
def get_sensor_types(cursor):
    query = (
        "SELECT sensor_type_id, sensor_type_name, sensor_type_low_controller_type_id, "
        "sensor_type_high_controller_type_id "
        "FROM sensor_type "
    )
    cursor.execute(query)
    sensor_types = {}
    for sensor_type_id, sensor_type_name, sensor_type_low_controller_type_id, sensor_type_high_controller_type_id \
            in cursor:
        sensor_types.update({sensor_type_id: {
            'sensor_type_name': sensor_type_name,
            'sensor_type_low_controller_type_id': sensor_type_low_controller_type_id,
            'sensor_type_high_controller_type_id': sensor_type_high_controller_type_id}})
    return sensor_types

def get_sensors(hub_id, cursor):
    query = (
        "SELECT sensor_id, sensor_gpio, sensor_type_id "
        "FROM sensor "
        "WHERE sensor.hub_id "
        "LIKE ('{}')".format(hub_id)
    )
    cursor.execute(query)
    sensor = []
    for sensor_id, sensor_gpio, sensor_type_id in cursor:
        sensor.append({
            'sensor_id': sensor_id,
            'sensor_gpio': sensor_gpio,
            'sensor_type_id': sensor_type_id})
    return sensor

def get_profile(hub_profile_id, cursor):
    query = (
        "SELECT profile_id, profile_name "
        "FROM profile "
        "WHERE profile.profile_id "
        "LIKE ({})".format(hub_profile_id)
    )
    cursor.execute(query)
    profile = {}
    for profile_id, profile_name in cursor:
        profile = {'profile_id': profile_id, 'profile_name': profile_name}
    return profile

def get_profile_sensor(hub_profile_id, cursor):
    query = (
        "SELECT profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_optimal, "
        "profile_sensor_high "
        "FROM profile_sensor "
        "WHERE profile_id "
        "LIKE ({})".format(str(hub_profile_id))
    )
    
    cursor.execute(query)
    profile_sensor = []
    for profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_optimal, profile_sensor_high in cursor:
        profile_sensor.append({
            'profile_sensor_id': profile_sensor_id,
            'profile_id': profile_id,
            'sensor_type_id': sensor_type_id,
            'profile_sensor_low': profile_sensor_low,
            'profile_sensor_optimal': profile_sensor_optimal,
            'profile_sensor_high': profile_sensor_high
        })
    return profile_sensor


#     query = (
#         "SELECT controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time  "
#         "FROM controller_type "
#     )
#     CURSOR.execute(query)
#     controller_types = {}
#     for controller_type_id, controller_type_name, controller_type_max_run_time, controller_type_min_rest_time in CURSOR:
#         controller_types.update({controller_type_id: {
#             'controller_type_name': controller_type_name,
#             'controller_type_max_run_time': controller_type_max_run_time,
#             'controller_type_min_rest_time': controller_type_min_rest_time}})
#     return controller_types



@app.route('/test')
def testHub():
    return 'hey'


@app.after_request
def addHeader(r):
    """
....Modify the headers to tell the browser to not cache any content
....for any response.
...."""

    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    r.headers['Expires'] = '0'
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



