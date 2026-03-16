import os
import sqlite3
from werkzeug.security import generate_password_hash

# Ensure the 'instance' folder exists
os.makedirs('instance', exist_ok=True)

# Use absolute path for reliability
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'campus.db')

# Connect to the database (it will be created if it doesn't exist)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# -- Create users table --
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        last_login TIMESTAMP,
        email TEXT NOT NULL UNIQUE,
        profile_image TEXT
    )
''')

# -- Create content table --
cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT,
        deadline DATE,
        semester TEXT NOT NULL,
        division TEXT NOT NULL,
        upload_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# -- Create a default admin user --
admin_username = 'admin'
admin_password = 'admin123'  # Change to a strong password in production
hashed_password = generate_password_hash(admin_password)

admin_email = 'admin@example.com' # Change this to your real email
try:
    cursor.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                   (admin_username, hashed_password, 'admin', admin_email))
    print(f"Admin user '{admin_username}' created successfully.")
except sqlite3.IntegrityError:
    print(f"Admin user '{admin_username}' already exists.")
# Commit changes and close the connection
conn.commit()
conn.close()

print(f"Database initialized successfully at: {db_path}")
