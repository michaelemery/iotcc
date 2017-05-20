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

CREATE TABLE controller (
    controller_id INT AUTO_INCREMENT PRIMARY KEY,
    controller_hub_id INT,
    controller_gpio INT,
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

CREATE TABLE sensor (
    sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_hub_id INT,
    sensor_gpio INT,
    sensor_type_id INT
);

CREATE TABLE profile (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_name VARCHAR(40) UNIQUE,
    profile_time_on TIME,
    profile_time_off TIME
);

CREATE TABLE profile_sensor (
    profile_sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT,
    sensor_type_id INT,
    profile_sensor_low INT,
    profile_sensor_high INT
);

CREATE TABLE event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_dtg TIMESTAMP,
    event_hub_id INT,
    event_profile_id INT,
    event_sensor_type_id INT,
    event_state INT,
    event_message VARCHAR(70)
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
    ('b8:27:eb:08:05:94', 'Hub Judd', 2, 2),
    ('b8:27:eb:bc:4d:a4', 'Hub Whiting', 3, 3);

INSERT INTO controller_type
    (controller_type_name, controller_type_max_run_time,
        controller_type_min_rest_time)
VALUES
    -- set controller names and limits (in seconds)
    ('Heater', '300', '120'),
    ('Cooling Fan', '900', '0'),
    ('Watering System', '5', '600');

INSERT INTO controller
    (controller_hub_id, controller_gpio, controller_type_id)
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

INSERT INTO sensor
    (sensor_hub_id, sensor_gpio, sensor_type_id)
VALUES
    (1, 17, 1),  -- emery   17 = temperature
    (1, 17, 2),  -- emery   17 = moisture
    (2, 27, 1),  -- judd    27 = temperature
    (2, 27, 2),  -- judd    27 = moisture
    (3, 22, 1),  -- whiting 22 = temperature
    (3, 22, 2);  -- whiting 22 = moisture

INSERT INTO profile
    (profile_name, profile_time_on, profile_time_off)
VALUES
    ('Desert Cacti', '08:00', '18:00'),
    ('Temperate Herb', '07:30', '17:30'),
    ('Tropical Fern', '07:00', '17:00');

INSERT INTO profile_sensor
    (profile_id, sensor_type_id, profile_sensor_low,
        profile_sensor_high)
VALUES
    -- set Temperate Herb temperature range
    (1, 1, 20, 25),
    -- set Temperate Herb moisture range
    (1, 2, 60, NULL),
    -- set Desert Cacti temperature range
    (2, 1, 22, 27),
    -- set Desert Cacti moisture range
    (2, 2, 59, NULL),
    -- set Tropical Fern temperature range
    (3, 1, 21, 26),
    -- set Tropical Fern moisture range
    (3, 2, 61, NULL);
