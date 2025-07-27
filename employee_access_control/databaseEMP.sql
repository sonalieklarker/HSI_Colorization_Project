CREATE DATABASE IF NOT EXISTS EMP;
USE EMP;

CREATE TABLE IF NOT EXISTS roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

INSERT IGNORE INTO roles (role_name) VALUES 
('Admin'), 
('Manager'), 
('Employee');

CREATE TABLE IF NOT EXISTS employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Insert employees with hashed passwords (stored as hex string to match Python hashlib.sha256 hexdigest)
INSERT IGNORE INTO employees (username, password, role_id) VALUES 
('admin_user', HEX(SHA2('adminpass', 256)), (SELECT id FROM roles WHERE role_name = 'Admin')),
('manager_user', HEX(SHA2('managerpass', 256)), (SELECT id FROM roles WHERE role_name = 'Manager')),
('employee_user', HEX(SHA2('employeepass', 256)), (SELECT id FROM roles WHERE role_name = 'Employee'));

CREATE TABLE IF NOT EXISTS aadmin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Insert admins, managers, employees in aadmin table with hashed passwords
INSERT IGNORE INTO aadmin (username, password, role_id) VALUES 
('admin', HEX(SHA2('admin123', 256)), (SELECT id FROM roles WHERE role_name = 'Admin')),
('manager', HEX(SHA2('manager123', 256)), (SELECT id FROM roles WHERE role_name = 'Manager')),
('employee', HEX(SHA2('employee123', 256)), (SELECT id FROM roles WHERE role_name = 'Employee'));

-- Check inserted data
SELECT * FROM employees;
SELECT * FROM aadmin;
