DROP DATABASE IF EXISTS microhort;

CREATE DATABASE microhort;

USE microhort;

CREATE TABLE owner (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_email VARCHAR(128) UNIQUE,
    owner_name VARCHAR(40)
);

CREATE TABLE hub (
    hub_id INT AUTO_INCREMENT PRIMARY KEY,
    hub_mac VARCHAR(40) UNIQUE,
    hub_name VARCHAR(40),
    hub_profile_id INT,
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
    hub_id INT,
    gpio INT,
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
    hub_id INT,
    gpio INT,
    sensor_type_id INT
);

CREATE TABLE profile (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_name VARCHAR(40) UNIQUE
);

CREATE TABLE profile_sensor (
    profile_sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT,
    sensor_type_id INT,
    sensor_low INT,
    sensor_optimal INT,
    sensor_high INT
);

CREATE TABLE datalog (
    datalog_id INT AUTO_INCREMENT PRIMARY KEY,
    dtg TIMESTAMP,
    hub_id INT, 
    profile_id INT,
    sensor_type_id INT,
    mean_sensor_value INT,
    controller_type_id INT,
    hub_controller_value INT
);

-- populate tables with test configuration

INSERT INTO owner 
    (owner_email, owner_name)
VALUES
    ('michael.foo@icloud.com', 'Michael Emery'),
    ('fookw@gmail.com', 'Karl Judd'),
    ('cliffordgfoo@gmail.com', 'Cliff Whiting');

INSERT INTO hub
    (hub_mac, hub_name, hub_profile_id, hub_owner_id)
VALUES
    ('b8:27:eb:0a:25:c5', 'Hub Emery', 1, 1),
    ('b8:27:eb:5f:70:91', 'Hub Judd', 2, 2),
    ('b8:27:eb:5f:70:92', 'Hub Whiting', 3, 3);

INSERT INTO controller_type
    (controller_type_name, controller_type_max_run_time,
        controller_type_min_rest_time)
VALUES
    -- set controller names and limits (in seconds)
    ('Heater', '300', '120'),
    ('Cooling Fan', '900', '0'),
    ('Watering System', '5', '600');

INSERT INTO hub_controller
    (hub_id, gpio, controller_type_id)
VALUES
    (1, 18, 1),  -- emery    18 = heater
    (1, 23, 2),  -- emery    23 = cooling fan
    (1, 24, 3),  -- emery    24 = watering system
    (2, 18, 1),  -- judd     25 = heater
    (2, 23, 2),  -- judd     12 = cooling fan
    (2, 24, 3),  -- judd     16 = watering system
    (3, 18, 1),  -- whiting  20 = heater
    (3, 23, 2),  -- whiting  21 = cooling fan
    (3, 24, 3);  -- whiting  26 = watering system

INSERT INTO sensor_type
    (sensor_type_name, sensor_type_low_controller_type_id, 
        sensor_type_high_controller_type_id)
VALUES
    -- set heater as low temperature controller and
    -- fan as high temperature controller for all test hubs
    ('Temperature', 1, 2),
    -- set watering system as low moisture controller for all
    -- test hubs, there is no (NULL) high moisture controller
    ('Moisture', 3, NULL);

INSERT INTO hub_sensor
    (hub_id, gpio, sensor_type_id)
VALUES
    (1, 17, 1),  -- emery   17 = temperature
    (1, 27, 2),  -- emery   27 = moisture
    (2,  5, 1),  -- judd     5 = temperature
    (2,  6, 2),  -- judd     6 = moisture
    (3, 13, 1),  -- whiting 13 = temperature
    (3, 19, 2);  -- whiting 19 = moisture

INSERT INTO profile
    (profile_name)
VALUES
    ('Temperate Herb'),
    ('Desert Cacti'),
    ('Tropical Fern');

INSERT INTO profile_sensor
    (profile_id, sensor_type_id, sensor_low, sensor_optimal,
        sensor_high)
VALUES
    -- set Desert Cacti temperature range to (2, 22, 30)
    (1, 1, 2, 22, 30),
    -- set Desert Cacti moisture range to (0, 5, NULL)
    (1, 2, 2, 10, NULL),
    -- set Temperate Ferns temperature range to (5, 20, 26)
    (2, 1, 5, 20, 26),
    -- set Temperate Ferns moisture range to (3, 10, NULL)
    (2, 2, 8, 15, NULL);
