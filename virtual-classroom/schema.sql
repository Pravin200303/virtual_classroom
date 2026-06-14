-- =====================================================================
-- Virtual Classroom Database Schema for MySQL / MySQL Workbench
-- =====================================================================

-- Create the database if it does not exist
CREATE DATABASE IF NOT EXISTS virtual_classroom;
USE virtual_classroom;

-- ---------------------------------------------------------------------
-- Table structure for table `users`
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'student' or 'instructor'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Table structure for table `courses`
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    instructor_id INT NOT NULL,
    category VARCHAR(100),
    thumbnail_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Table structure for table `enrollments`
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Table structure for table `materials`
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_key VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_type VARCHAR(100) NOT NULL, -- 'video', 'pdf', 'slides', or 'document'
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =====================================================================
-- Optional Sample Data (Useful for Testing)
-- =====================================================================

-- Note: The password hash below corresponds to 'password123' hashed with Werkzeug (pbkdf2:sha256)
-- You can log in using these accounts once your environment is configured!

INSERT INTO users (name, email, password_hash, role) VALUES 
('John Instructor', 'instructor@example.com', 'pbkdf2:sha256:260000$l7a4x3aH44Q7o5w1$169e5d4cb0f496fb10b240ffcdde68fec501a3556cc6b8c8d8b9e6fa4efd6e07', 'instructor'),
('Jane Student', 'student@example.com', 'pbkdf2:sha256:260000$l7a4x3aH44Q7o5w1$169e5d4cb0f496fb10b240ffcdde68fec501a3556cc6b8c8d8b9e6fa4efd6e07', 'student')
ON DUPLICATE KEY UPDATE name=name;

-- Sample Course (associated with John Instructor, ID = 1)
INSERT INTO courses (id, title, description, instructor_id, category, thumbnail_url) VALUES
(1, 'Introduction to Python Programming', 'Learn the basics of Python, including data structures, loops, functions, and object-oriented programming.', 1, 'Programming', '/static/css/images/default-course.png')
ON DUPLICATE KEY UPDATE title=title;

-- Enroll Jane Student (ID = 2) into the python course (ID = 1)
INSERT INTO enrollments (student_id, course_id) VALUES
(2, 1)
ON DUPLICATE KEY UPDATE student_id=student_id;

-- Sample Material for the course
INSERT INTO materials (course_id, title, file_key, file_url, file_type) VALUES
(1, 'Course Syllabus PDF', 'materials/syllabus_demo.pdf', '/static/uploads/materials/syllabus_demo.pdf', 'pdf')
ON DUPLICATE KEY UPDATE title=title;
