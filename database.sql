

USE job_finder;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    password VARCHAR(255),
    user_type ENUM('employee', 'employer') NOT NULL
);

-- Drop the incorrect table first (if exists)
DROP TABLE IF EXISTS jobs;

-- Create the corrected jobs table
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    email VARCHAR(100),  
    phone VARCHAR(20),
    address VARCHAR(255),
    duration VARCHAR(100),
    employer_id INT NOT NULL, 
    FOREIGN KEY (employer_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE job_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    employee_id INT NOT NULL,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE
);

