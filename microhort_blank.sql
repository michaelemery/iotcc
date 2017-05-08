DROP DATABASE microhort;

CREATE DATABASE microhort;

USE microhort;

CREATE TABLE owner (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_email VARCHAR(128) UNIQUE,
    owner_nickname VARCHAR(40)
);

CREATE TABLE hub (
    hub_id INT AUTO_INCREMENT PRIMARY KEY,
    hub_mac VARCHAR(40) UNIQUE,
    hub_name VARCHAR(40),
    hub_owner_id INT
);

CREATE TABLE controller_type (
    controller_type_id INT AUTO_INCREMENT PRIMARY KEY,
    controller_type_name VARCHAR(40) UNIQUE,
    /* set controller maximum safe running time 
       (in seconds) before it must be turned off */
    controller_type_max_run_time INT,
    /* set controller minimum resting time 
       (in seconds) before it can safely restart */
    controller_type_min_rest_time INT
);

CREATE TABLE hub_controller (
    hub_controller_id INT AUTO_INCREMENT PRIMARY KEY,
    hub_id VARCHAR(18),
    hub_gpio INT,
    controller_type_id INT
);

CREATE TABLE sensor_type (
    sensor_type_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_type_name VARCHAR(40) UNIQUE,
    /* set controller type for correcting
       low sensor readings */
    sensor_type_low_controller_type_id INT,
    /* set controller type for correcting
       high sensor readings */
    sensor_type_high_controller_type_id INT
);

CREATE TABLE hub_sensor (
    hub_sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    hub_id VARCHAR(18),
    hub_gpio INT,
    sensor_type_id INT
);

CREATE TABLE environment (
    environment_id INT AUTO_INCREMENT PRIMARY KEY,
    environment_name VARCHAR(40) UNIQUE
);

CREATE TABLE environment_sensor (
    environment_sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    environment_id INT,
    sensor_id INT,
    sensor_low INT,
    sensor_optimal INT,
    sensor_high INT
);

CREATE TABLE datalog (
    datalog_id INT AUTO_INCREMENT PRIMARY KEY,
    dtg TIMESTAMP,
    hub_mac VARCHAR(18), 
    environment_id INT,
    sensor_type_id INT,
    mean_sensor_value INT,
    controller_type_id INT,
    hub_controller_value INT
);