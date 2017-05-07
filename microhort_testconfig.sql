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
    sensor_type_low_controller_id INT,
    /* set controller type for correcting
       high sensor readings */
    sensor_type_high_controller_id INT
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

-- populate tables with test configuration

INSERT INTO owner
    (owner_email, owner_nickname)
VALUES
('michael.emery@icloud.com', 'Michael Emery'),
('juddkw@gmail.com', 'Karl Judd'),
('cliffordgwhiting@gmail.com', 'Cliff Whiting');

INSERT INTO hub
    (hub_mac, hub_name, hub_owner_id)
VALUES
    ('b8:27:eb:5f:70:90', 'Hub Emery', 
     SELECT owner.owner_id 
     FROM owner
     WHERE owner.owner_email = 'michael.emery@icloud.com'),
    ('b8:27:eb:5f:70:91', 'Hub Judd', 
     SELECT owner.owner_id 
     FROM owner
     WHERE owner.owner_email = 'juddkw@gmail.com'),
    ('b8:27:eb:5f:70:92', 'Hub Whiting', 
     SELECT owner.owner_id 
     FROM owner
     WHERE owner.owner_email = 'cliffordgwhiting@gmail.com');

INSERT INTO controller_type
    (controller_type_name, controller_type_max_run_time,
        controller_type_min_rest_time)
VALUES
    ('Cooling Fan', '900', '0'),
    ('Heater', '300', '120'),
    ('watering system', '5', '600');

INSERT INTO hub_controller
    (hub_id, hub_gpio, controller_type_id)
VALUES
    -- set gpio 18 to heater controller for Michael's hub
    (SELECT owner.hub_id
     FROM owner
     WHERE owner.owner_email = 'michael.emery@icloud.com',
     18,
     SELECT controller_type.controller_type_id 
     FROM controller_type
     WHERE controller_type_name = 'Heater'),
    -- set gpio 23 to mist spray controller for Michael's hub
    (SELECT owner.hub_id
     FROM owner
     WHERE owner.owner_email = 'michael.emery@icloud.com',
     23,
     SELECT controller_type.controller_type_id 
     FROM controller_type
     WHERE controller_type_name = 'Water Spray');

INSERT INTO sensor_type
    (sensor_type_name, sensor_type_low_controller_id, 
        sensor_type_high_controller_type_id)
VALUES
    ('Temperature',
     -- set heater as low temperature controller 
     SELECT controller_type.controller_type_id 
     FROM controller_type
     WHERE controller_type.controller_type_name = 
        'Heater',
     -- set cooling fan as temperature controller
     SELECT controller_type.controller_type_id 
     FROM controller_type
     WHERE controller_type.controller_type_name = 
        'Cooling Fan',
    ('Moisture',
     -- set mist spray as low moisture controller
     SELECT controller_type.controller_type_id 
     FROM controller_type
     WHERE controller_type.controller_type_name = 
        'Water Spray',
     -- there is no high moisture controller 
     NULL);

INSERT INTO hub_sensor
    (hub_id, hub_gpio, sensor_type)
VALUES
    -- set gpio 17 to temperature sensor for Michael's hub
    (SELECT owner.hub_id
     FROM owner
     WHERE owner.owner_email = 'michael.emery@icloud.com',
     17, 
     SELECT sensor_type.sensor_type_id 
     FROM sensor_type
     WHERE sensor_type_name = 'Temperature'),
    -- set gpio 27 to moisture sensor for Michael's hub
    (SELECT owner.hub_id
     FROM owner
     WHERE owner.owner_email = 'michael.emery@icloud.com',
     27, 
     SELECT sensor_type.sensor_type_id 
     FROM sensor_type
     WHERE sensor_type_name = 'Moisture');

INSERT INTO environment
    (environment_name)
VALUES
    ('Desert Cacti'),
    ('Temperate Ferns');

INSERT INTO environment_sensor
    (environment_id, sensor_id, sensor_low, sensor_optimal,
        sensor_high)
VALUES
    (SELECT environment_id
     FROM environment.environment_id
     WHERE environment_name = 'Desert Cacti',
     SELECT sensor.sensor_id
     FROM sensor
     WHERE sensor.sensor_name = 'Temperature',
     2, 22, 30),
    (SELECT environment_id
     FROM environment.environment_id
     WHERE environment_name = 'Temperate Ferns',
     SELECT sensor.sensor_id
     FROM sensor
     WHERE sensor.sensor_name = 'Temperature',
     5, 20, 26);  

