import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import db_service
import s3_service

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'virtual_classroom_secret_key_123')

# Initialize DB tables
with app.app_context():
    try:
        db_service.init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

# --- Middleware & Decorators ---

@app.before_request
def load_logged_in_user():
    """Loads the logged-in user from the database into Flask's application context 'g'."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        try:
            g.user = db_service.get_user_by_id(user_id)
        except Exception:
            g.user = None
            session.clear()

def login_required(view):
    """Decorator to require login for specific routes."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

def instructor_required(view):
    """Decorator to require instructor permissions."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        if g.user.get('role') != 'instructor':
            flash("Access denied. Instructors only.", "danger")
            return redirect(url_for('dashboard'))
        return view(**kwargs)
    return wrapped_view

# --- Routes ---

@app.route('/')
def index():
    """Public landing page."""
    if g.user:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration."""
    if g.user:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') # 'student' or 'instructor'
        
        if not name or not email or not password or not role:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))
            
        if role not in ['student', 'instructor']:
            flash("Invalid role selected.", "danger")
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        try:
            # Check if user already exists
            existing_user = db_service.get_user_by_email(email)
            if existing_user:
                flash("An account with that email already exists.", "danger")
                return redirect(url_for('register'))
                
            db_service.create_user(name, email, hashed_password, role)
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Registration Error: {e}")
            flash("An error occurred during registration. Please try again.", "danger")
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user authentication."""
    if g.user:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for('login'))
            
        try:
            user = db_service.get_user_by_email(email)
            if user and check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                flash(f"Welcome back, {user['name']}!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            print(f"Login Error: {e}")
            flash("An error occurred during login. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main user portal displaying courses and analytics based on user role."""
    try:
        if g.user['role'] == 'instructor':
            # Instructor Dashboard
            my_courses = db_service.get_courses_by_instructor(g.user['id'])
            
            # Simple Instructor Analytics
            total_students_enrolled = 0
            for c in my_courses:
                # Count enrollments for each course by querying DB
                # For basic analytics we can check how many students enrolled overall
                res = db_service.execute_query(
                    "SELECT COUNT(*) as count FROM enrollments WHERE course_id = %s",
                    (c['id'],), fetchone=True
                )
                c['student_count'] = res['count'] if res else 0
                total_students_enrolled += c['student_count']
                
            analytics = {
                'total_courses': len(my_courses),
                'total_students': total_students_enrolled,
                'role': 'instructor'
            }
            return render_template('dashboard.html', courses=my_courses, analytics=analytics)
            
        else:
            # Student Dashboard
            enrolled_courses = db_service.get_courses_by_student(g.user['id'])
            all_courses = db_service.get_courses()
            
            # Filter out courses student is already enrolled in
            enrolled_ids = {c['id'] for c in enrolled_courses}
            available_courses = [c for c in all_courses if c['id'] not in enrolled_ids]
            
            analytics = {
                'enrolled_count': len(enrolled_courses),
                'available_count': len(available_courses),
                'role': 'student'
            }
            return render_template('dashboard.html', 
                                   enrolled_courses=enrolled_courses, 
                                   available_courses=available_courses, 
                                   analytics=analytics)
    except Exception as e:
        print(f"Dashboard Load Error: {e}")
        flash("An error occurred while loading your dashboard.", "danger")
        return render_template('dashboard.html', courses=[], analytics={})

@app.route('/create-course', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_course():
    """Allows instructors to create courses and upload optional thumbnails."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        thumbnail = request.files.get('thumbnail')
        
        if not title or not description or not category:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('create_course'))
            
        thumbnail_url = None
        if thumbnail and thumbnail.filename != '':
            # Upload thumbnail file to S3/Local
            _, thumbnail_url = s3_service.upload_file(thumbnail, folder='thumbnails')
            
        # Default fallback thumbnail if not uploaded
        if not thumbnail_url:
            thumbnail_url = "/static/css/images/default-course.png"
            
        try:
            db_service.create_course(title, description, g.user['id'], category, thumbnail_url)
            flash("Course created successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"Course Creation Error: {e}")
            flash("Failed to create course. Please try again.", "danger")
            
    return render_template('create_course.html')

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    """Displays course contents, files, lectures, and upload form for instructors."""
    try:
        course = db_service.get_course(course_id)
        if not course:
            flash("Course not found.", "danger")
            return redirect(url_for('dashboard'))
            
        is_instructor = (g.user['role'] == 'instructor' and course['instructor_id'] == g.user['id'])
        enrolled = db_service.is_enrolled(g.user['id'], course_id) or is_instructor
        
        materials = []
        if enrolled:
            materials = db_service.get_materials_by_course(course_id)
            
        return render_template('course.html', 
                               course=course, 
                               enrolled=enrolled, 
                               is_instructor=is_instructor, 
                               materials=materials)
    except Exception as e:
        print(f"Course View Error: {e}")
        flash("An error occurred while loading course details.", "danger")
        return redirect(url_for('dashboard'))

@app.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    """Enrolls a student in a course."""
    if g.user['role'] != 'student':
        flash("Only students can enroll in courses.", "danger")
        return redirect(url_for('dashboard'))
        
    try:
        # Check if already enrolled
        if db_service.is_enrolled(g.user['id'], course_id):
            flash("You are already enrolled in this course.", "info")
        else:
            db_service.enroll_student(g.user['id'], course_id)
            flash("Enrolled successfully! Welcome to the course.", "success")
    except Exception as e:
        print(f"Enrollment Error: {e}")
        flash("Failed to enroll in the course.", "danger")
        
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/course/<int:course_id>/add-material', methods=['POST'])
@login_required
@instructor_required
def add_material(course_id):
    """Allows an instructor to upload PDFs or lecture videos to S3 and save metadata in RDS."""
    try:
        course = db_service.get_course(course_id)
        if not course or course['instructor_id'] != g.user['id']:
            flash("Unauthorized access.", "danger")
            return redirect(url_for('dashboard'))
            
        title = request.form.get('title')
        material_file = request.files.get('file')
        
        if not title or not material_file or material_file.filename == '':
            flash("Please provide a title and select a file to upload.", "danger")
            return redirect(url_for('course_detail', course_id=course_id))
            
        # Determine file type based on extension
        filename = material_file.filename.lower()
        if filename.endswith(('.mp4', '.mkv', '.webm', '.avi')):
            file_type = 'video'
        elif filename.endswith('.pdf'):
            file_type = 'pdf'
        elif filename.endswith(('.ppt', '.pptx')):
            file_type = 'slides'
        else:
            file_type = 'document'
            
        # Upload material to S3/Local
        file_key, file_url = s3_service.upload_file(material_file, folder='materials')
        
        if file_key and file_url:
            db_service.add_material(course_id, title, file_key, file_url, file_type)
            flash("Material uploaded and added successfully!", "success")
        else:
            flash("Failed to upload the file.", "danger")
            
    except Exception as e:
        print(f"Material Upload Error: {e}")
        flash("An error occurred during file upload.", "danger")
        
    return redirect(url_for('course_detail', course_id=course_id))

if __name__ == '__main__':
    # Run development server
    app.run(host='0.0.0.0', port=5000, debug=True)
