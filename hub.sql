CREATE DATABASE microhort;

USE microhort;

CREATE TABLE controller (
    controller_id INT AUTO_INCREMENT PRIMARY KEY,
    controller_type VARCHAR(40)
);

CREATE TABLE sensor (
    sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_type VARCHAR(40),
    low_description VARCHAR(40),
    low_control_id INT,
    high_description VARCHAR(40),
    high_control_id INT
);

CREATE TABLE plant_profile (
    plant_profile_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT,
    sensor_low_value INT,
    sensor_optimal_value INT,
    sensor_high_value INT
);

CREATE TABLE plant_type (
    plant_type_id INT AUTO_INCREMENT PRIMARY KEY,
    plant_type_description VARCHAR(40)
);

CREATE TABLE datalog (
    datalog_id INT AUTO_INCREMENT PRIMARY KEY,
    hub_mac VARCHAR(18),
    post_dtg TIMESTAMP,
    event_description VARCHAR(255)
);

CREATE TABLE hub_sensor (
    hub_sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT,
    gpio INT
);

CREATE TABLE hub_controller (
    hub_controller_id INT AUTO_INCREMENT PRIMARY KEY,
    controller_id INT,
    gpio INT
);
