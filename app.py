import os
import pytz # Using pytz for timezone handling
from datetime import datetime, timedelta # Added timedelta for calculating 3/7 months
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

# --- App Configuration ---
app = Flask(__name__)

# Ensure instance folder exists
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
instance_folder = os.path.join(BASE_DIR, 'instance')
os.makedirs(instance_folder, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_folder, 'campus.db')
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['PROFILE_PIC_FOLDER'] = os.path.join(BASE_DIR, 'profile_pics')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- MAIL CONFIGURATION (Update with your details) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'campusmateadap1234@gmail.com'
app.config['MAIL_PASSWORD'] = 'pjmz cuft qyox xqul' 
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'ppt', 'pptx'}

# --- Initialize extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Create Folders ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['PROFILE_PIC_FOLDER']):
    os.makedirs(app.config['PROFILE_PIC_FOLDER'])

# --- Models ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'faculty'
    last_login = db.Column(db.DateTime)
    email = db.Column(db.String(150), unique=True, nullable=False)
    profile_image = db.Column(db.String(300), nullable=True)
    uploads = db.relationship('Content', backref='author', lazy=True)

class Content(db.Model):
    __tablename__ = 'content'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(300))
    deadline = db.Column(db.Date)
    semester = db.Column(db.String(100), nullable=False) 
    division = db.Column(db.String(50), nullable=False)
    # Use lambda to get current IST time on insertion
    upload_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.timezone("Asia/Kolkata")))

# --- Helper Functions ---
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('ist')
def format_datetime_ist(dt):
    if dt is None:
        return "Never"
    ist = pytz.timezone("Asia/Kolkata")
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(ist).strftime('%d-%b-%Y %I:%M %p')

# --- UPDATED: Advanced Auto-Delete Logic ---
def cleanup_old_content():
    """
    Deletes:
    - Notices and Events older than 3 months (90 days).
    - Notes, Timetables, and Assignments older than 7 months (210 days).
    """
    try:
        ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
        
        # 1. Short-term cleanup (3 months / 90 days)
        cutoff_3_months = ist_now - timedelta(days=90)
        old_items_3m = Content.query.filter(
            Content.content_type.in_(['notice', 'event']),
            Content.upload_date < cutoff_3_months
        ).all()

        # 2. Long-term cleanup (7 months / 210 days)
        cutoff_7_months = ist_now - timedelta(days=210)
        old_items_7m = Content.query.filter(
            Content.content_type.in_(['notes', 'timetable', 'assignment']),
            Content.upload_date < cutoff_7_months
        ).all()
        
        # Combine lists
        items_to_delete = old_items_3m + old_items_7m
        
        if items_to_delete:
            print(f"Cleaning up {len(items_to_delete)} old items...")
            for item in items_to_delete:
                # Delete physical file
                if item.file_path:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.file_path))
                    except OSError:
                        pass
                # Delete DB record
                db.session.delete(item)
            
            db.session.commit()
            print("Cleanup complete.")
            
    except Exception as e:
        print(f"Cleanup error: {e}")

# --- Routes ---

@app.route('/')
def student_dashboard():
    # Run cleanup every time the dashboard is loaded
    cleanup_old_content()
    
    selected_sem = request.args.get('semester', type=str) 
    selected_div = request.args.get('division', type=str)

    content_data = {
        'notice': [],
        'notes': {},
        'assignment': {},
        'timetable': [],
        'event': []
    }

    if selected_sem and selected_div:
        content_types = ['timetable', 'notes', 'assignment', 'event', 'notice']
        for c_type in content_types:
            query = Content.query.filter(
               Content.content_type == c_type,
               Content.semester.like(f'%{selected_sem}%'),
               Content.division.like(f'%{selected_div}%')
            ).order_by(Content.upload_date.desc()).all()
            
            if c_type in ['notes', 'assignment']:
                faculty_content = {}
                for item in query:
                    author_name = item.author.username
                    faculty_content.setdefault(author_name, []).append(item)
                content_data[c_type] = faculty_content
            else:
                content_data[c_type] = query

    return render_template('student_dashboard.html', content=content_data, sem=selected_sem, div=selected_div)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}_dashboard"))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Update last login to IST
            user.last_login = datetime.now(pytz.timezone("Asia/Kolkata"))
            db.session.commit()
            flash('Logged in successfully!', 'success')
            return redirect(url_for(f'{user.role}_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_dashboard'))
    return render_template('faculty_dashboard.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('faculty_dashboard'))
    return render_template('admin_dashboard.html')

@app.route('/your_uploads')
@app.route('/your_uploads/<int:user_id>') 
@login_required
def your_uploads(user_id=None):
    target_user_id = current_user.id
    title_text = "Your Uploaded Content"
    
    if user_id and current_user.role == 'admin':
        target_user = db.session.get(User, user_id)
        if target_user:
            target_user_id = user_id
            title_text = f"Uploads by {target_user.username}"
    
    uploads = Content.query.filter_by(user_id=target_user_id).order_by(Content.upload_date.desc()).all()
    return render_template('your_uploads.html', uploads=uploads, title_text=title_text)

@app.route('/upload', methods=['POST'])
@login_required
def upload_content():
    content_type = request.form['content_type']
    title = request.form['title']
    description = request.form['description']
    
    selected_semesters = request.form.getlist('semester')
    semester_str = ",".join(selected_semesters)
    selected_divisions = request.form.getlist('division')
    division_str = ",".join(selected_divisions)
    
    deadline = request.form.get('deadline')
    file = request.files.get('file')

    file_path = None
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Use IST time for filename uniqueness
        ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
        unique_filename = f"{ist_now.strftime('%Y%m%d%H%M%S')}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        file_path = unique_filename

    new_content = Content(
        user_id=current_user.id,
        content_type=content_type,
        title=title,
        description=description,
        file_path=file_path,
        deadline=datetime.strptime(deadline, '%Y-%m-%d').date() if deadline else None,
        semester=semester_str,
        division=division_str
    )
    db.session.add(new_content)
    db.session.commit()
    flash(f'{content_type.capitalize()} uploaded successfully!', 'success')
    
    # Redirect to the correct dashboard
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('faculty_dashboard'))

@app.route('/update/<int:content_id>', methods=['GET', 'POST'])
@login_required
def update_content(content_id):
    content_to_update = Content.query.get_or_404(content_id)
    
    if content_to_update.user_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to edit this content.', 'danger')
        return redirect(url_for('your_uploads'))
        
    if request.method == 'POST':
        content_to_update.title = request.form['title']
        content_to_update.description = request.form['description']
        
        content_to_update.semester = ",".join(request.form.getlist('semester'))
        content_to_update.division = ",".join(request.form.getlist('division'))
        
        if 'deadline' in request.form:
            deadline_str = request.form.get('deadline')
            content_to_update.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

        file = request.files.get('file')
        if file and file.filename != '' and allowed_file(file.filename):
            if content_to_update.file_path:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], content_to_update.file_path))
                except OSError:
                    pass 
            
            filename = secure_filename(file.filename)
            ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
            unique_filename = f"{ist_now.strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            content_to_update.file_path = unique_filename

        db.session.commit()
        flash('Content updated successfully!', 'success')
        return redirect(url_for('your_uploads'))
        
    return render_template('update_content.html', content=content_to_update)

@app.route('/delete/<int:content_id>', methods=['POST'])
@login_required
def delete_content(content_id):
    content = Content.query.get_or_404(content_id)
    if content.user_id == current_user.id or current_user.role == 'admin':
        if content.file_path:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], content.file_path))
            except OSError:
                pass
        db.session.delete(content)
        db.session.commit()
        flash('Content deleted successfully.', 'success')
    else:
        flash('Permission denied.', 'danger')
    return redirect(url_for('your_uploads'))

@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('faculty_dashboard'))

    if request.method == 'POST':
        if 'add_user' in request.form:
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            email = request.form['email']

            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()

            if existing_user:
                flash('Username or email already exists.', 'warning')
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password, role=role, email=email)
                db.session.add(new_user)
                db.session.commit()

                try:
                    msg = Message('Welcome to CampusMate!',
                                  sender=app.config['MAIL_USERNAME'],
                                  recipients=[email])
                    msg.body = f"Hello {username},\n\nYou have been added to the CampusMate platform as a {role} by the admin.\n\nYour login details are:\nUsername: {username}\nPassword: {password}\n\nYou can login at: {url_for('login', _external=True)}\n\nRegards,\nThe CampusMate Team"
                    mail.send(msg)
                    flash('User added successfully and notification email sent!', 'success')
                except Exception as e:
                    flash(f'User added, but email failed to send. Error: {e}', 'warning')

        elif 'remove_user' in request.form:
            user_id_str = request.form['user_id']
            try:
                user_id = int(user_id_str)
                user_to_remove = db.session.get(User, user_id)
                if user_to_remove:
                    if user_to_remove.profile_image:
                        try:
                            os.remove(os.path.join(app.config['PROFILE_PIC_FOLDER'], user_to_remove.profile_image))
                        except OSError:
                            pass
                    Content.query.filter_by(user_id=user_id).delete()
                    db.session.delete(user_to_remove)
                    db.session.commit()
                    flash('User removed successfully.', 'success')
                else:
                    flash('User not found.', 'danger')
            except ValueError:
                flash('Invalid user ID.', 'danger')
        return redirect(url_for('manage_users'))

    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        file = request.files.get('profile_pic')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
            unique_filename = f"{ist_now.strftime('%Y%m%d%H%M%S')}_{current_user.id}_{filename}"
            file_path = os.path.join(app.config['PROFILE_PIC_FOLDER'], unique_filename)

            if current_user.profile_image:
                try:
                    os.remove(os.path.join(app.config['PROFILE_PIC_FOLDER'], current_user.profile_image))
                except OSError:
                    pass

            file.save(file_path)
            current_user.profile_image = unique_filename
            db.session.commit()
            flash('Profile picture updated!', 'success')
        else:
            flash('Invalid file type or no file selected.', 'warning')
    return render_template('profile.html')

@app.route('/remove_profile_pic', methods=['POST'])
@login_required
def remove_profile_pic():
    if current_user.profile_image:
        file_path = os.path.join(app.config['PROFILE_PIC_FOLDER'], current_user.profile_image)
        try:
            os.remove(file_path)
        except OSError:
            pass
        current_user.profile_image = None
        db.session.commit()
        flash('Profile picture removed successfully.', 'success')
    return redirect(url_for('profile'))

@app.route('/profile_pics/<filename>')
def serve_profile_pic(filename):
    return send_from_directory(app.config['PROFILE_PIC_FOLDER'], filename)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(current_user.password, old_password):
            flash('Incorrect old password.', 'danger')
            return redirect(url_for('change_password'))
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'warning')
            return redirect(url_for('change_password'))

        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for(f'{current_user.role}_dashboard'))
        
    return render_template('change_password.html')

@app.route('/uploads/<filename>')
#@login_required
def serve_file(filename):
    # Check file extension to determine if it should be viewed inline or downloaded
    file_extension = os.path.splitext(filename)[1].lower()
    viewable_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
    
    should_download = file_extension not in viewable_extensions
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=should_download
    )

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)