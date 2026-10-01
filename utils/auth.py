import random
import string
from functools import wraps
from flask import session, redirect, url_for, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from utils.database import get_db_connection

def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

def generate_anonymous_id():
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"CB-{suffix}"

def login_user_session(user):
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    session['anonymous_id'] = user['anonymous_id']

def logout_user_session():
    session.clear()

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT id, anonymous_id, name, email, age_group, gender_optional, contact_pref, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                flash("Access denied: insufficient permissions.", "danger")
                if user_role == 'survivor':
                    return redirect(url_for('survivor_dashboard'))
                elif user_role == 'counselor':
                    return redirect(url_for('counselor_dashboard'))
                elif user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
