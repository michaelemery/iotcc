#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response, render_template, flash, url_for, redirect, session, abort
import mysql.connector
import json
import platform
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from MySQLdb import escape_string as thwart
from functools import wraps
import gc

# TODO - make sure to remove sensitive info from Exceptions & turn debug mode off!

app = Flask(__name__)
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
    return render_template("dashboard.html")

@app.route('/testjsonresponse/')
def testJsonResponse():
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

def getDbCursor():
    connection = mysql.connector.connect(user='iotcc_user',password='158335danish',host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com',database='microhort')
    cursor = connection.cursor()
    return connection, cursor
    
def cleanUpDb(connection, cursor):
    cursor.close()
    connection.close()
    
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
    if not any(sensor):
        print("No configured sensors. Add sensors then restart.\n")
        exit()
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

########################################################################################################
# User registration classes
########################################################################################################

# @app.route('/login/', methods=["POST", "GET"])
# def loginPage():
#     error = ""
#     try:
#         if request.method == "POST":
#             attempted_username = request.form["username"]
#             attempted_password = request.form["password"]  
#             flash(attempted_username)
#             flash(attempted_password)
#             #check username in db, and hashed password. Compare with 
#             if attempted_username == "admin" and attempted_password == "password":
#                 return redirect(url_for('dashBoardPage'))
#             else:
#                 flash("INVALID LOGIN")
#                 error = "Invalid login. Try Again."
#         return render_template("login.html", error=error) #fallthrough covers GET aswell.
#     except Exception as e:

#         # TODO - this needs to be changed to allow less information.
#         flash(str(e))
#         return render_template("login.html", error=error)
#     return ""

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
            if (result is not None and result[2] == password):
                session['logged_in'] = True
                session['username'] = username
                flash("Welcome " + username + " you are now logged in.")
                gc.collect()
                conn.close()
                return redirect(url_for('dashBoardPage'))
            #verification failed. falls through to here.
            flash("INVALID LOGIN")
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
            conn.close()
            gc.collect()
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashBoardPage'))
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    session.clear() # removes all cookies.
    flash("You have been logged out")
    gc.collect()
    return redirect(url_for("homePage"))


@app.route("/manage")
@login_required
def manage():
    return (session["username"])



    # try:
    #     form = RegistrationForm(request.form)
    #     if request.method == "POST" and form.validate():
    #         username  = form.username.data
    #         email = form.email.data
    #         password = form.password.data
    #         conn, c = getDbCursor()
    #         x = c.execute("SELECT * FROM users WHERE username = '{}'".format(thwart(username)))

    #         if int(x) > 0:
    #             flash("That username is already taken, please choose another")
    #             return render_template('register.html', form=form)

    #         else:
    #             query = """INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"""
    #             c.execute(query, (thwart(username), thwart(password), thwart(email),))
                
    #             conn.commit()
    #             flash("Thanks for registering!")
    #             c.close()
    #             conn.close()
    #             gc.collect()

    #             session['logged_in'] = True
    #             session['username'] = username

    #             return redirect(url_for('dashBoard'))

    #     return render_template("register.html", form=form)

    # except Exception as e:
    #     return(str(e))

########################################################################################################
# Error handling
########################################################################################################

@app.errorhandler(404)
def pageNotFound(e):
     return render_template("404.html")

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



