import os
import sqlite3
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Determine if MySQL should be used
USE_MYSQL = all([
    os.getenv('DB_HOST'),
    os.getenv('DB_USER'),
    os.getenv('DB_PASSWORD'),
    os.getenv('DB_NAME')
])

def get_connection():
    """Returns a database connection based on environment configurations."""
    if USE_MYSQL:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3307))
        )
    else:
        conn = sqlite3.connect('classroom.db')
        conn.row_factory = sqlite3.Row
        # Enable foreign key support for SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def execute_query(query, params=(), commit=True, fetchall=False, fetchone=False):
    """Executes a query and handles database connection lifecycle.
    Adapts %s parameters to ? when using SQLite.
    """
    conn = get_connection()
    cursor = None
    try:
        if USE_MYSQL:
            cursor = conn.cursor(dictionary=True)
        else:
            cursor = conn.cursor()
            # Convert %s placeholders to SQLite ? placeholders
            query = query.replace('%s', '?')

        cursor.execute(query, params)
        
        result = None
        if fetchall:
            if USE_MYSQL:
                result = cursor.fetchall()
            else:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
        elif fetchone:
            if USE_MYSQL:
                result = cursor.fetchone()
            else:
                row = cursor.fetchone()
                result = dict(row) if row else None
        else:
            if commit:
                conn.commit()
            result = cursor.lastrowid
            
        return result
    except Exception as e:
        if commit:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        if cursor:
            cursor.close()
        conn.close()

def init_db():
    """Initializes the database tables depending on the engine."""
    if USE_MYSQL:
        # Create MySQL tables
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE KEY unique_enrollment (student_id, course_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                file_key VARCHAR(255) NOT NULL,
                file_url TEXT NOT NULL,
                file_type VARCHAR(100) NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ]
    else:
        # Create SQLite tables
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                instructor_id INTEGER NOT NULL,
                category TEXT,
                thumbnail_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE(student_id, course_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_key TEXT NOT NULL,
                file_url TEXT NOT NULL,
                file_type TEXT NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
            """
        ]
    
    # We execute each query inside an active connection
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for query in queries:
            cursor.execute(query)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# --- DB Service Functions ---

def create_user(name, email, password_hash, role):
    query = "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)"
    return execute_query(query, (name, email, password_hash, role))

def get_user_by_email(email):
    query = "SELECT * FROM users WHERE email = %s"
    return execute_query(query, (email,), fetchone=True)

def get_user_by_id(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    return execute_query(query, (user_id,), fetchone=True)

def create_course(title, description, instructor_id, category, thumbnail_url):
    query = "INSERT INTO courses (title, description, instructor_id, category, thumbnail_url) VALUES (%s, %s, %s, %s, %s)"
    return execute_query(query, (title, description, instructor_id, category, thumbnail_url))

def get_courses():
    query = """
        SELECT c.*, u.name as instructor_name 
        FROM courses c 
        JOIN users u ON c.instructor_id = u.id 
        ORDER BY c.created_at DESC
    """
    return execute_query(query, fetchall=True)

def get_course(course_id):
    query = """
        SELECT c.*, u.name as instructor_name 
        FROM courses c 
        JOIN users u ON c.instructor_id = u.id 
        WHERE c.id = %s
    """
    return execute_query(query, (course_id,), fetchone=True)

def get_courses_by_instructor(instructor_id):
    query = "SELECT * FROM courses WHERE instructor_id = %s ORDER BY created_at DESC"
    return execute_query(query, (instructor_id,), fetchall=True)

def get_courses_by_student(student_id):
    query = """
        SELECT c.*, u.name as instructor_name, e.enrolled_at 
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        JOIN users u ON c.instructor_id = u.id
        WHERE e.student_id = %s 
        ORDER BY e.enrolled_at DESC
    """
    return execute_query(query, (student_id,), fetchall=True)

def enroll_student(student_id, course_id):
    query = "INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)"
    return execute_query(query, (student_id, course_id))

def is_enrolled(student_id, course_id):
    query = "SELECT 1 FROM enrollments WHERE student_id = %s AND course_id = %s"
    res = execute_query(query, (student_id, course_id), fetchone=True)
    return res is not None

def add_material(course_id, title, file_key, file_url, file_type):
    query = "INSERT INTO materials (course_id, title, file_key, file_url, file_type) VALUES (%s, %s, %s, %s, %s)"
    return execute_query(query, (course_id, title, file_key, file_url, file_type))

def get_materials_by_course(course_id):
    query = "SELECT * FROM materials WHERE course_id = %s ORDER BY uploaded_at ASC"
    return execute_query(query, (course_id,), fetchall=True)
