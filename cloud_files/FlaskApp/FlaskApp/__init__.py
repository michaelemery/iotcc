#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response, render_template, flash, url_for, redirect, session, abort
import mysql.connector
import json
import platform
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from MySQLdb import escape_string as thwart
from functools import wraps
from dbFunctions import cleanUpDb, getDbCursor 
import gc
import botoupload


# TODO - make sure to remove sensitive info from Exceptions & turn debug mode off!

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SECRET_KEY'] = '158335microhort' 


########################################################################################################
# Decorators
########################################################################################################

## TO USE LOGIN_REQUIRED
# place annotation below the route declaration
# @app.route("/logout")
# @login_required

def login_required(f): # decorator wraps the function. it runs wrap() first, to see if the user has a "logged_in" session in cookies.
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs) #arguments and keyword arguments.
        else:
            flash("You need to log in to view this.")
            #currently just redirects to login page. no reference to previous page...
            return redirect(url_for('loginPage'))
    return wrap


def hid_required(f): # decorator wraps the function. it runs wrap() first, to see if the user has a "hid" session in cookies.
    @wraps(f)
    def wrap(*args, **kwargs):
        if "hid" in session:
            return f(*args, **kwargs) #arguments and keyword arguments.
        else:
            flash("You need to select an environment before you can do this!")
            return redirect(url_for('dashBoardPage'))
    return wrap

#opposite of the above decorator. User must be logged out.
def logged_out_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            flash("You can't do that.")
            return redirect(url_for('homePage'))
        else:
            return f(*args, **kwargs) #arguments and keyword arguments.
    return wrap

@app.route('/')
def homePage():
    # version = platform.python_version()
    # return '158335 MicroHort project. Running on python' + version
    return render_template("main.html") #template renders from /templates/ 

@app.route('/dashboard/')
@login_required
def dashBoardPage():
    # get all environments belonging to the user.
    connection, cursor = getDbCursor()
    query = (
        "SELECT hub_id, hub_name "
        "FROM hub "
        "WHERE hub_owner_id = {}".format(int(session["id"]))
    )
    cursor.execute(query)
    results = {}
    for hub_id,hub_name in cursor:
       results[hub_id] = hub_name
    cleanUpDb(connection,cursor)
    gc.collect()
    # these environments are rendered on the dashboard.html template.
    return render_template("dashboard.html", results=results)

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

########################################################################################################
# Handling new device
########################################################################################################

@app.route('/newdevice', methods=["POST"])
@login_required
def newDevice():

    user_id = session["id"]

    if request.form["name"] == "":
        flash("You must type in a name!", "error")
        return redirect(url_for('dashBoardPage'))
    
    if request.form["uid"] == "":
        flash("You must type in a unique id!", "error")
        return redirect(url_for('dashBoardPage'))

    name = request.form["name"]
    try:
        unique_id = int(request.form["uid"])
    except Exception:
        flash("Unique ID must be a number!", "error")
        return redirect(url_for('dashBoardPage'))

    # check database for hub
    connection, cursor = getDbCursor()
    query = (
        "SELECT hub_id, hub_mac, hub_name, hub_profile_id, hub_owner_id "
        "FROM hub "
        "WHERE hub_id = {}".format(unique_id)
    )
    cursor.execute(query)
    result = cursor.fetchone()
    if result is None:
        flash("That unique ID doesn't exist!", "error")
        return redirect(url_for('dashBoardPage'))
    
    if result[4] is not None: # hub_owner_id
        flash("That hub is already owned", "error")
        return redirect(url_for('dashBoardPage'))
    
    # if it makes it here, there is a valid hub with no owner.
    # update its name, and set the owner to be this user
    # UPDATES DEFAULT PLANT PROFILE TO 1.
    query = (
        "UPDATE hub "
        "SET hub_name = %s, hub_profile_id = 1, hub_owner_id = %s "
        "WHERE hub_id = %s"
    )
    
    cursor.execute(query, (name, user_id, unique_id))
    connection.commit()

    cleanUpDb(connection, cursor)
    gc.collect()

    #redirect back to dashboard for now.
    flash("Successfully added in environment " + name, "success")
    #TODO -- add Try: catch: here?
    return redirect(url_for('dashBoardPage'))

########################################################################################################
# Handling devices
########################################################################################################

@app.route('/viewdevice', methods=["GET"])
@login_required
def viewDevice():
    # try:
    # Get the id parameter from the GET request
    # OR if user has already chosen a hub, just use that one.
    args = request.args.to_dict()
    if "hid" in args:
        hid = args["hid"]
    elif "hid" in session:
        hid = session["hid"]
        
    #query db here for general info
    connection, cursor = getDbCursor()
    hub = get_hub_from_id(hid, cursor)
    info = {
        'hub' : hub,
        'controller_type': get_controller_types(cursor),
        'controller': get_controllers(hub['hub_id'],cursor),
        'sensor_type': get_sensor_types(cursor),
        'sensor': get_sensors(hub['hub_id'],cursor),
        'profile': get_profile(hub['hub_profile_id'],cursor),
        'profile_sensor': get_profile_sensor(hub['hub_profile_id'],cursor),
        'lighting_gpio': get_lighting(hub['hub_profile_id'],cursor)
    }

    cleanUpDb(connection, cursor)
    gc.collect()

    if hub["hub_owner_id"] != session["id"]:

        return redirect(url_for('forbiddenPage'))
    # get environment name
    environment_name = info["hub"]["hub_name"]
        
    # get plant profile
    plant_profile = info["profile"]["profile_name"]

    #get sensors
    sensors = {}
    for sensor in info["sensor"]:
        sensors[sensor["sensor_id"]] = (info["sensor_type"][(sensor["sensor_type_id"])]["sensor_type_name"])
        
    #get controllers
    
    control_elements = {}
    for ce in info["controller"]:
        control_elements[ce["controller_id"]] = (info["controller_type"][(ce["controller_type_id"])]["controller_type_name"])

    print ("control elements: " + str(control_elements))

    # except Exception:
    #     # TODO - return a failed device page
    #     return("Failed to get device.")

    # add new session variables
    session["hid"] = hid
    session["environment_name"] = environment_name
    session["current_profile"] = plant_profile
    return render_template("viewdevice.html", environment_name=environment_name, plant_profile=plant_profile, sensors=sensors, control_elements=control_elements) #hid is appended to every sub url, it lets the system query the correct hub.



########################################################################################################
# Sensors/CE
########################################################################################################

@app.route('/removesensor', methods=["POST"])
@login_required
@hid_required
def deleteSensor():
    # retrieve information
    hid = session["hid"]
    sensor_name = request.form["sensor"]
    sensor_id = int(request.form["sensor_id"])

    # remove the sensor from the sensors table
    connection, cursor = getDbCursor()
    query = (
        "DELETE FROM sensor "
        "WHERE sensor_id = %s"
    )
    cursor.execute(query, (sensor_id,))
    connection.commit()
    cleanUpDb(connection, cursor)
    gc.collect()
    
    flash ('You have successfully removed the ' + sensor_name + ' sensor.', 'success')
    return redirect(url_for('viewDevice'))

@app.route('/removecontroller', methods=["POST"])
@login_required
@hid_required 
def deleteController():
    # retrieve information
    hid = session["hid"]
    controller_name = request.form["ce"]
    controller_id = int(request.form["ce_id"])

    # remove the sensor from the sensors table
    connection, cursor = getDbCursor()
    query = (
        "DELETE FROM controller "
        "WHERE controller_id = %s"
    )
    cursor.execute(query, (controller_id,))
    connection.commit()
    cleanUpDb(connection, cursor)
    gc.collect()
    
    flash ('You have successfully removed the ' + controller_name + ' controller.', 'success')
    return redirect(url_for('viewDevice'))

@app.route('/selectsensor') #takes user to a page to select the sensor
@login_required
@hid_required
def selectSensor():
    flash("NOTE: for the raspberry pi, slot 1 = GPIO 5, 2 = GPIO 6, 3 = GPIO 13, 4 = GPIO 17, 5 = GPIO 22, 6 = GPIO 27")
    SENSOR_MAPPING = { 5:1, 6:2, 13:3, 17:4, 22:5, 27:6
    }
    # retrieve hub id for future queries
    hid = session["hid"]

    connection, cursor = getDbCursor()
    # get possible sensors
    query = (
        "SELECT sensor_type_id, sensor_type_name "
        "FROM sensor_type"
    )
    cursor.execute(query)
    sensors = {}
    for sensor_type_id, sensor_type_name in cursor:
        sensors[sensor_type_id] = sensor_type_name

    cleanUpDb(connection, cursor)
    gc.collect()
    # return a list of current profiles to the user
    return render_template("selectsensor.html", sensors=sensors)


@app.route('/addsensor', methods=["POST"]) #looks at POST params to add the sensor.
@login_required
@hid_required
def addSensor():
    PORT_MAPPING = { 1:5, 2:6, 3:13, 4:17, 5:22, 6:27} # maps ports to GPIO on rpi.

    # retrieve information
    hid = int(session["hid"])

    try:
        port = int(request.form["port"])
        sensor_type_name = request.form["sensor_type_name"]
        sensor_type_id = int(request.form["sensor_type_id"]) #from hidden form field in /selectsensor.html
    except Exception:
        flash("You need to select a port", "error")
        return redirect(url_for('viewDevice'))
    
    # get the gpio pin associated with the port
    gpio = PORT_MAPPING[port]

    #add the new sensor to the GPIO table.
    connection, cursor = getDbCursor()
    query = (
        "INSERT INTO sensor (sensor_hub_id,sensor_gpio,sensor_type_id)"
        "VALUES ({}, {}, {}) ".format(hid, gpio, sensor_type_id)
    )
    cursor.execute(query)
    connection.commit()
    cleanUpDb(connection, cursor)
    gc.collect()

    flash("You have successfully added a " + sensor_type_name + " sensor to port " + str(port), "success")
    return redirect(url_for('viewDevice'))


@app.route('/selectcontroller') #takes user to a page to select the sensor
@login_required
@hid_required
def selectControl():
    flash("NOTE: for the raspberry pi, slot 7 = GPIO 12, 8 = GPIO 16, 9 = GPIO 18, 10 = GPIO 23, 11 = GPIO 24, 12 = GPIO 25")
    SENSOR_MAPPING = { 12:7, 16:8, 18:9, 23:10, 24:11, 25:12 }
    # retrieve hub id for future queries
    hid = session["hid"]

    connection, cursor = getDbCursor()
    # get possible sensors
    query = (
        "SELECT controller_type_id, controller_type_name "
        "FROM controller_type"
    )
    cursor.execute(query)
    controllers = {}
    for controller_type_id, controller_type_name in cursor:
        controllers[controller_type_id] = controller_type_name
    cleanUpDb(connection, cursor)
    gc.collect()
    # return a list of current profiles to the user
    return render_template("selectcontrol.html", controllers=controllers)


@app.route('/addcontroller', methods=["POST"]) #looks at POST params to add the controller.
@login_required
@hid_required
def addControl():
    PORT_MAPPING = { 7:12, 8:16, 9:18, 10:23, 11:24, 12:25 } # maps ports to GPIO on rpi.

    # retrieve information
    hid = int(session["hid"])
    try:
        port = int(request.form["port"])
        controller_type_name = request.form["controller_type_name"]
        controller_type_id = int(request.form["controller_type_id"]) #from hidden form field
    except Exception:
        flash("You need to select a port", "error")
        return redirect(url_for('viewDevice'))
        
    # get the gpio pin associated with the port
    gpio = PORT_MAPPING[port]

    #add the new controller to the GPIO table.
    connection, cursor = getDbCursor()
    query = (
        "INSERT INTO controller (controller_hub_id,controller_gpio,controller_type_id) "
        "VALUES ({}, {}, {}) ".format(hid, gpio, controller_type_id)
    )
    cursor.execute(query)
    connection.commit()
    cleanUpDb(connection, cursor)
    gc.collect()

    flash("You have successfully added a " + controller_type_name + " controller to port " + str(port), "success")
    return redirect(url_for('viewDevice'))

########################################################################################################
# plant profiles
########################################################################################################

@app.route('/modifyplantprofile', methods=["GET"])
@login_required
@hid_required
def modifyPlantProfile():
    # the user requies a hub to be selected to be here!
    # this means use of hid & profile cookie can be used.
    connection, cursor = getDbCursor()
    query = (
        "SELECT profile_id, profile_name "
        "FROM profile"
    )

    cursor.execute(query)
    profiles = {}
    for profile_id, profile_name in cursor:
        profiles[profile_id] = profile_name
    cleanUpDb(connection, cursor)
    gc.collect()
    # return a list of current profiles to the user
    return render_template("modifyplantprofile.html", profiles=profiles)

@app.route('/selectplantprofile', methods=["GET"])
@login_required
@hid_required
def selectPlantProfile():
    #get the pid argument. (plant profile id)
    args = request.args.to_dict()
    profile_id = args["pid"]
    hub_id = session["hid"]
    #TODO - check pid exists.
    #convert to int.
    profile_id = int(profile_id)
    # set the plant profile for the user to the one from the request URL
    connection, cursor = getDbCursor()
    query = (
        "UPDATE hub "
        "SET hub_profile_id = {} "
        "WHERE hub_id = {}".format(profile_id, hub_id)
    )
    cursor.execute(query)
    connection.commit()
    flash("You have successfully updated your plant profile", "success")
    return redirect(url_for('viewDevice'))
    #redirect user to viewdevice


########################################################################################################
# COMING SOON PAGES
########################################################################################################
@app.route('/comingsoon/')
def comingSoonPage():
    return render_template("comingsoon.html")

@app.route('/shop/')
def shopPage():
    return render_template("comingsoon.html")

@app.route('/cart/')
def cartPage():
    return render_template("comingsoon.html")

@app.route('/devices/')
def devicesPage():
    return render_template("comingsoon.html")

@app.route('/accessories/')
def accessoriesPage():
    return render_template("comingsoon.html")

########################################################################################################
# GET CONFIG !!!!
########################################################################################################

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
        'controller': get_controllers(hub['hub_id'],cursor),
        'sensor_type': get_sensor_types(cursor),
        'sensor': get_sensors(hub['hub_id'],cursor),
        'profile': get_profile(hub['hub_profile_id'],cursor),
        'profile_sensor': get_profile_sensor(hub['hub_profile_id'],cursor),
        'lighting_gpio': get_lighting(hub['hub_profile_id'],cursor)
    }
    #return the config as a JSON object
    #TODO -- set content-type to JSON here.
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

def get_hub_from_id(id,cursor):
    query = (
        "SELECT hub_id, hub_mac, hub_name, hub_profile_id, hub_owner_id "
        "FROM hub "
        "WHERE hub_id "
        "LIKE ('{}')".format(id)
    )
    cursor.execute(query)
    hub = {}
    for hub_id, hub_mac, hub_name, hub_profile_id, hub_owner_id in cursor:
        hub.update({
            'hub_id': hub_id,
            'hub_mac': hub_mac,
            'hub_name': hub_name,
            'hub_profile_id': hub_profile_id,
            'hub_owner_id': hub_owner_id})
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
        "WHERE controller_hub_id "
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
        "WHERE sensor_hub_id "
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
        "SELECT profile_id, profile_name, profile_lighting_on, profile_lighting_off "
        "FROM profile "
        "WHERE profile.profile_id "
        "LIKE ({})".format(hub_profile_id)
    )
    cursor.execute(query)
    profile = {}
    for profile_id, profile_name, profile_lighting_on, profile_lighting_off in cursor:
        profile = {
            'profile_id': profile_id,
            'profile_name': profile_name,
            'profile_lighting_on': profile_lighting_on,
            'profile_lighting_off': profile_lighting_off}
    return profile

def get_profile_sensor(hub_profile_id, cursor):    
    query = (
        "SELECT profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_high "
        "FROM profile_sensor "
        "WHERE profile_id "
        "LIKE ({})".format(str(hub_profile_id))
    )
    cursor.execute(query)
    profile_sensor = {}
    for profile_sensor_id, profile_id, sensor_type_id, profile_sensor_low, profile_sensor_high in cursor:
        profile_sensor.update({
            sensor_type_id: {
                'profile_sensor_low': profile_sensor_low,
                'profile_sensor_high': profile_sensor_high
            }
        })
    return profile_sensor

# return lighting ports
def get_lighting(hub_profile_id, cursor):
    query = (
        "SELECT lighting_id, lighting_hub_id, lighting_gpio "
        "FROM lighting "
        "WHERE lighting_hub_id "
        "LIKE ({})".format(str(hub_profile_id))
    )
    cursor.execute(query)
    lighting = []
    for lighting_id, lighting_hub_id, lighting_gpio in cursor:
        lighting.append(lighting_gpio)
    return lighting

@app.route('/login/', methods=["POST", "GET"])
@logged_out_required
def loginPage():
    error = ""
    try:
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            conn,cursor = getDbCursor()
            query = 'SELECT * FROM users WHERE username = %s'
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            print(result)
            if (result is not None and result[2] == password):
                session['id'] = result[0]
                session['logged_in'] = True
                session['username'] = username
                flash("Welcome " + username + " you are now logged in.", "success")
                gc.collect()
                conn.close()
                return redirect(url_for('dashBoardPage'))
            #verification failed. falls through to here.
            flash("INVALID LOGIN", "error")
            error = "Invalid login. Try Again."
            gc.collect()
            conn.close()
        return render_template("login.html", error=error) #fallthrough covers GET aswell.
    except Exception as e:
        # TODO - this needs to be changed to allow less information.
        flash(str(e))
        return render_template("login.html", error=error)

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

def flash_errors(form):
    # function flashes errors from any WTForm
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), "error")

@app.route('/register/', methods=["GET","POST"])
@logged_out_required
def registerPage():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        conn,cursor = getDbCursor()
        print("username " + username)
        query = 'SELECT * FROM users WHERE username = %s'
        cursor.execute(query, (username,))
        if cursor.fetchone() is not None:
            flash("Sorry that username is already taken.")
            gc.collect()
            conn.close()
            return render_template("register.html", form=form)
        else: 
            query = """INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"""
            cursor.execute(query, (username, password, email,))
            conn.commit()
            session['logged_in'] = True
            session['username'] = username
            query = 'SELECT * FROM users WHERE username = %s'
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            session['id'] = result[0]
            conn.close()
            gc.collect()
            return redirect(url_for('dashBoardPage'))
    if request.method == "POST" and form.validate() != True:
        flash_errors(form)
        return render_template("register.html", form=form)
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    session.clear() # removes all cookies.
    flash("You have been logged out")
    gc.collect()
    return redirect(url_for("homePage"))



########################################################################################################
# HTTP REST picutres
########################################################################################################

@app.route('/imageupload', methods=["POST"])
def imageUpload():
    # get the hub ID from the params

    S3_BUCKET_URL = "https://s3-us-west-2.amazonaws.com/microhort/pictures/"

    f = request.files['file']
    filename = request.form['filename']
    description = request.form['description']
    mac = request.form['mac']

    #upload the file to s3 bucket
    # the file will upload to ../pictures/filename
    # this link will be saved in the database, mapping to the hub_id.
    botoupload.uploadFileToMicroHortS3(f, filename)

    #save the file to the database
    connection, cursor = getDbCursor()
    
    # get the owner of the hub && hub_id
    query = (
        "SELECT hub_id, hub_owner_id "
        "FROM hub "
        "WHERE hub_mac "
        "LIKE ('{}')".format(mac)
    )
    cursor.execute(query)
    hub_id = cursor.fetchone()[1]

    link = S3_BUCKET_URL + filename
    # save to pictures table.
    query = (
        "INSERT INTO pictures (hub_id,link,description) "
        "VALUES (%s, %s, %s)"
    )
    cursor.execute(query, (hub_id, link, description))
    connection.commit()
    cleanUpDb(connection,cursor)
    gc.collect()
    # return a success message.
    return ("success")

@app.route('/viewpictures')
# @login_required
# @hid_required
def viewPictures():
    #get the user's selected hub
    hid = session["hid"]
    #retrieve the picture links for all the files.
    # -- store these inside of a list.

    # remove the sensor from the sensors table
    connection, cursor = getDbCursor()
    query = (
        "SELECT link, description "
        "FROM pictures "
        "WHERE hub_id = %s"
    )
    cursor.execute(query, (hid,))

    results = []

    for link, desc in cursor:
        results.append((link,desc))

    cleanUpDb(connection, cursor)
    gc.collect()
    #embed the pictures into the page

    # test data (overrides DB call...)
    # results = [("https://www.w3schools.com//w3images/lights.jpg", "1"), ("https://www.w3schools.com//w3images/lights.jpg", "2"),("https://www.w3schools.com//w3images/lights.jpg", "3"),("https://www.w3schools.com//w3images/lights.jpg", "4"),("https://www.w3schools.com//w3images/lights.jpg", "5")]

    environment_name = session["environment_name"] 
    is_results = True
    if len(results) == 0:
        is_results = False
    print(is_results)

    return render_template("viewpictures.html", environment_name=environment_name, pictures=results, is_results=str(is_results))

########################################################################################################
# DATA LOGS
########################################################################################################
@app.route('/submitdatalog', methods=['POST'])
def dataLog():

    log = request.form['log']
    log_dict = json.loads(log)
    # event_id, event_dtg, event_hub_id, event_profile_id, event_sensor_type_id, event_state, event_message


    # #save the file to the database
    connection, cursor = getDbCursor()

    query = (
        "INSERT INTO event (event_dtg, event_hub_id, event_profile_id, event_sensor_type_id, event_state, event_message) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    cursor.execute(query, (str(log_dict["event_dtg"]), str(log_dict["event_hub_id"]), str(log_dict["event_profile_id"]), str(log_dict["event_sensor_type_id"]), str(log_dict["event_state"]), str(log_dict["event_message"])))
    connection.commit()
    cleanUpDb(connection,cursor)

    return "success"

@app.route('/events')
@login_required
@hid_required
def viewEvents():

    hid = session["hid"]
    environment_name = session["environment_name"]
    # query DB for all events with a event_hub_id of hid

    query = (
        "SELECT event_dtg, event_message "
        "FROM event "
        "WHERE event_hub_id = %s"
    )
    # #save the file to the database
    connection, cursor = getDbCursor()

    cursor.execute(query, (hid,))

    results = []
    for event_dtg, event_message in cursor:
        results.append((event_dtg, event_message))

    # Currently first LOGGED TO THE DB will be displayed first.
    # we want most recent.

    results = list(reversed(results))
    cleanUpDb(connection,cursor)

    return render_template("events.html", results=results, environment_name=environment_name)



########################################################################################################
# Error & access handling
########################################################################################################

@app.errorhandler(404)
def pageNotFound(e):
    return render_template("404.html")

@app.errorhandler(400)
def pageNotFound(e):
    return "Not sure what went wrong there. If it was submitting information, try again."

@app.errorhandler(405)
def pageNotFound(e):
    return render_template("forbidden.html")

@app.route("/forbidden")
def forbiddenPage():
    return render_template("forbidden.html")
    

########################################################################################################
# HTTP Modifiers
########################################################################################################

# @app.after_request
# def addHeader(r):
#     """
# ....Modify the headers to tell the browser to not cache any content
# ....for any response.
# ...."""

#     r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     r.headers['Pragma'] = 'no-cache'
#     r.headers['Expires'] = '0'
#     r.headers['Cache-Control'] = 'public, max-age=0'
#     return r

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



