import sqlite3
import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import datetime

DB_FILE = "users.db"
ADMIN_EMAIL = "samer.el.sayegh@gmail.com"

def init_db():
    """Initialize the users database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL, -- 'pending', 'approved', 'rejected'
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Ensure Admin account exists (auto-approved)
    # Use a default password or require manual setup. 
    # For simplicity, we'll check if admin exists, if not create with 'admin123' (CHANGE THIS IN PROD)
    c.execute("SELECT * FROM users WHERE email = ?", (ADMIN_EMAIL,))
    if not c.fetchone():
        # Create default admin
        print(f"Creating default admin account for {ADMIN_EMAIL}")
        pwd_hash = hash_password("admin123")
        c.execute("INSERT INTO users (email, password_hash, status, is_admin) VALUES (?, ?, ?, 1)",
                  (ADMIN_EMAIL, pwd_hash, 'approved'))
        
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    """Verify a stored password against one provided by user."""
    return stored_password_hash == hashlib.sha256(provided_password.encode()).hexdigest()

def register_user(email, password):
    """Register a new user. Returns (Success: bool, Message: str)."""
    init_db() # Ensure DB exists
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # Check if user exists
        c.execute("SELECT email FROM users WHERE email = ?", (email,))
        if c.fetchone():
            return False, "User already exists."
        
        pwd_hash = hash_password(password)
        # Default status is 'pending'
        c.execute("INSERT INTO users (email, password_hash, status) VALUES (?, ?, ?)",
                  (email, pwd_hash, 'pending'))
        conn.commit()
        
        # Try sending email
        send_approval_request_email(email)
        
        return True, "Registration successful. Please wait for admin approval."
    except Exception as e:
        return False, f"Error registering user: {e}"
    finally:
        conn.close()

def authenticate_user(email, password):
    """
    Authenticate a user. 
    Returns: (user_data: dict, error_message: str)
    user_data is None if auth fails.
    """
    init_db()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return None, "User not found."
    
    if not verify_password(user['password_hash'], password):
        return None, "Incorrect password."
    
    if user['status'] != 'approved':
        return None, "Account is pending approval."
        
    return dict(user), None

def get_pending_users():
    """Get list of users waiting for approval."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT email, created_at FROM users WHERE status = 'pending'")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return users

def approve_user(email):
    """Approve a pending user."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET status = 'approved' WHERE email = ?", (email,))
    conn.commit()
    conn.close()

def send_approval_request_email(new_user_email):
    """
    Send an email to the admin notifying them of a new signup.
    Requires st.secrets or environment variables for SMTP.
    """
    # Try to get credentials from st.secrets first, then os.environ
    email_user = None
    email_pass = None
    
    try:
        if "EMAIL_USER" in st.secrets:
             email_user = st.secrets["EMAIL_USER"]
             email_pass = st.secrets["EMAIL_PASS"]
    except:
        pass # st.secrets might not be set up
        
    if not email_user:
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")
        
    if not email_user or not email_pass:
        print("WARNING: Email credentials not found. Skipping email notification.")
        return

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = ADMIN_EMAIL
    msg['Subject'] = "New User Registration Request"
    
    body = f"""
    A new user has registered and is awaiting approval.
    
    Email: {new_user_email}
    Timestamp: {datetime.datetime.now()}
    
    Please log in to the dashboard to approve them.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Assuming Gmail for now, logic can be adjusted
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_pass)
        text = msg.as_string()
        server.sendmail(email_user, ADMIN_EMAIL, text)
        server.quit()
        print(f"Approval email sent to {ADMIN_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Initialize (safe to call on import)
init_db()
