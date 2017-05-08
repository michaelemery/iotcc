DROP DATABASE IF EXISTS microhort;

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
    hub_id INT,
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
    hub_id INT,
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
    hub_id INT, 
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
    ('b8:27:eb:5f:70:90', 'Hub Emery', 1),
    ('b8:27:eb:5f:70:91', 'Hub Judd', 2),
    ('b8:27:eb:5f:70:92', 'Hub Whiting', 3);

INSERT INTO controller_type
    (controller_type_name, controller_type_max_run_time,
        controller_type_min_rest_time)
VALUES
    -- set controller names and limits (in seconds)
    ('Heater', '300', '120'),
    ('Cooling Fan', '900', '0'),
    ('Watering System', '5', '600');

INSERT INTO hub_controller
    (hub_id, hub_gpio, controller_type_id)
VALUES
    -- set gpio 18 to heater controller for all test hubs
    (1, 18, 1),
    (2, 18, 1),
    (3, 18, 1),
    -- set gpio 23 to cooling controller for all test hubs
    (1, 23, 2),
    (2, 23, 2),
    (3, 23, 2),
    -- set gpio 24 to water controller for all test hubs
    (1, 24, 3),
    (2, 24, 3),
    (3, 24, 3);

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
    (hub_id, hub_gpio, sensor_type_id)
VALUES
    -- set gpio 17 to temperature sensor for all test hubs
    (1, 17, 1),
    (2, 17, 1),
    (3, 17, 1),
    -- set gpio 27 to moisture sensor for all test hubs
    (1, 27, 2),
    (2, 27, 2),
    (3, 27, 2);

INSERT INTO environment
    (environment_name)
VALUES
    ('Desert Cacti'),
    ('Temperate Ferns');

INSERT INTO environment_sensor
    (environment_id, sensor_id, sensor_low, sensor_optimal,
        sensor_high)
VALUES
    -- set Desert Cacti temperature range to (2, 22, 30)
    (1, 1, 2, 22, 30),
    -- set Temperate Ferns temperature range to (5, 20, 26)
    (2, 1, 5, 20, 26),
        -- set Desert Cacti moisture range to (0, 5, NULL)
    (1, 1, 2, 10, NULL),
    -- set Temperate Ferns moisture range to (3, 10, NULL)
    (2, 1, 8, 15, NULL);
