import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from utils.database import init_db, seed_demo_data, get_db_connection
from utils.auth import (
    hash_password, verify_password, generate_anonymous_id,
    login_user_session, logout_user_session, get_current_user,
    login_required, role_required
)
from utils.prediction import (
    predict_distress_indicator, calculate_previous_checkin_score,
    evaluate_early_warning_rules, get_model_metrics
)
from utils.translations import LANGUAGES, translate, is_rtl
from models.train_model import train_and_save_model

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'carebridge-secure-hackathon-key-2026-privacy-first')

# Initialize DB and seed demo data on app startup
with app.app_context():
    init_db()
    # Train model if not present
    metrics = get_model_metrics()
    if not metrics:
        train_and_save_model()
    seed_demo_data()

@app.context_processor
def inject_user_and_translations():
    current_lang = session.get('lang', 'en')
    return {
        'current_user': get_current_user(),
        'current_lang': current_lang,
        'languages': LANGUAGES,
        'is_rtl': is_rtl(current_lang),
        '_t': lambda key: translate(key, current_lang)
    }

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in LANGUAGES:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'survivor':
            return redirect(url_for('survivor_dashboard'))
        elif role in ['counselor', 'admin']:
            return redirect(url_for('counselor_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter both email/ID and password.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE email = ? OR anonymous_id = ?
        ''', (identifier, identifier)).fetchone()
        conn.close()

        if user and verify_password(user['password_hash'], password):
            login_user_session(user)
            flash(f"Welcome back, {user['name']}!", "success")
            if user['role'] == 'survivor':
                return redirect(url_for('survivor_dashboard'))
            elif user['role'] == 'counselor':
                return redirect(url_for('counselor_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid email/anonymous ID or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('survivor_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        age_group = request.form.get('age_group', '')
        gender = request.form.get('gender', 'Prefer not to say')
        contact_pref = request.form.get('contact_pref', 'App Notification')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not age_group or not password:
            flash("Please complete all required fields.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email address already exists.", "danger")
            return render_template('register.html')

        anon_id = generate_anonymous_id()
        pwd_hash = hash_password(password)

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (anonymous_id, name, email, age_group, gender_optional, contact_pref, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'survivor')
        ''', (anon_id, name, email, age_group, gender, contact_pref, pwd_hash))
        new_user_id = cursor.lastrowid
        conn.commit()

        user = conn.execute("SELECT * FROM users WHERE id = ?", (new_user_id,)).fetchone()
        conn.close()

        login_user_session(user)
        flash(f"Account created! Your private Anonymous ID is {anon_id}.", "success")
        return redirect(url_for('survivor_dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user_session()
    flash("You have been safely logged out.", "info")
    return redirect(url_for('login'))

# ==========================================
# SURVIVOR ROUTES
# ==========================================

@app.route('/survivor/dashboard')
@login_required
@role_required('survivor')
def survivor_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Latest check-in
    latest_checkin = conn.execute('''
        SELECT * FROM checkins WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
    ''', (user_id,)).fetchone()

    # Total check-in count
    total_checkins = conn.execute('''
        SELECT COUNT(*) as count FROM checkins WHERE user_id = ?
    ''', (user_id,)).fetchone()['count']

    # Recent 5 check-ins
    recent_checkins = conn.execute('''
        SELECT * FROM checkins WHERE user_id = ? ORDER BY created_at DESC LIMIT 5
    ''', (user_id,)).fetchall()

    # Active resources
    resources = conn.execute('''
        SELECT * FROM support_resources ORDER BY id ASC LIMIT 3
    ''', ()).fetchall()

    conn.close()

    # Format result details for latest check-in
    latest_analysis = None
    if latest_checkin:
        latest_analysis = predict_distress_indicator(
            latest_checkin['stress_score'],
            latest_checkin['sleep_score'],
            latest_checkin['concentration_score'],
            latest_checkin['social_support_score'],
            latest_checkin['distress_frequency'],
            latest_checkin['previous_checkin_score'] or 5.0
        )

    return render_template('survivor_dashboard.html',
                           latest_checkin=latest_checkin,
                           total_checkins=total_checkins,
                           recent_checkins=recent_checkins,
                           resources=resources,
                           latest_analysis=latest_analysis)

@app.route('/survivor/checkin', methods=['GET', 'POST'])
@login_required
@role_required('survivor')
def checkin():
    user_id = session['user_id']

    if request.method == 'POST':
        try:
            stress = int(request.form.get('stress_score', 5))
            sleep = int(request.form.get('sleep_score', 5))
            concentration = int(request.form.get('concentration_score', 5))
            social_support = int(request.form.get('social_support_score', 5))
            distress_freq = int(request.form.get('distress_frequency', 5))
        except (ValueError, TypeError):
            flash("Invalid input values provided. Please enter scores between 1 and 10.", "danger")
            return redirect(url_for('checkin'))

        # Calculate previous score
        prev_score = calculate_previous_checkin_score(user_id)

        # Predict distress indicator
        prediction_result = predict_distress_indicator(stress, sleep, concentration, social_support, distress_freq, prev_score)
        predicted_indicator = prediction_result['indicator']
        confidence = prediction_result['confidence']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO checkins (user_id, stress_score, sleep_score, concentration_score, social_support_score, distress_frequency, previous_checkin_score, predicted_indicator, predicted_probability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, stress, sleep, concentration, social_support, distress_freq, prev_score, predicted_indicator, confidence))
        new_checkin_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Evaluate early warnings rules
        checkin_dict = {
            'stress_score': stress,
            'sleep_score': sleep,
            'predicted_indicator': predicted_indicator
        }
        alert_reason = evaluate_early_warning_rules(user_id, checkin_dict)

        flash("Daily well-being check-in submitted successfully.", "success")
        return redirect(url_for('checkin_result', checkin_id=new_checkin_id))

    return render_template('checkin.html')

@app.route('/survivor/checkin/result/<int:checkin_id>')
@login_required
@role_required('survivor')
def checkin_result(checkin_id):
    user_id = session['user_id']
    conn = get_db_connection()
    checkin = conn.execute('''
        SELECT * FROM checkins WHERE id = ? AND user_id = ?
    ''', (checkin_id, user_id)).fetchone()
    conn.close()

    if not checkin:
        flash("Check-in record not found.", "warning")
        return redirect(url_for('survivor_dashboard'))

    analysis = predict_distress_indicator(
        checkin['stress_score'],
        checkin['sleep_score'],
        checkin['concentration_score'],
        checkin['social_support_score'],
        checkin['distress_frequency'],
        checkin['previous_checkin_score'] or 5.0
    )

    return render_template('checkin_result.html', checkin=checkin, analysis=analysis)

@app.route('/survivor/history')
@login_required
@role_required('survivor')
def survivor_history():
    user_id = session['user_id']
    conn = get_db_connection()
    checkins = conn.execute('''
        SELECT * FROM checkins WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('history.html', checkins=checkins)

@app.route('/survivor/support')
@login_required
def survivor_support():
    conn = get_db_connection()
    resources = conn.execute("SELECT * FROM support_resources ORDER BY category ASC, id ASC").fetchall()
    conn.close()
    return render_template('support.html', resources=resources)

# ==========================================
# COUNSELOR ROUTES
# ==========================================

@app.route('/counselor/dashboard')
@login_required
@role_required('counselor', 'admin')
def counselor_dashboard():
    conn = get_db_connection()

    # Metrics
    total_survivors = conn.execute("SELECT COUNT(*) FROM users WHERE role='survivor'").fetchone()[0]
    recent_checkins_count = conn.execute("SELECT COUNT(*) FROM checkins WHERE created_at >= date('now', '-7 days')").fetchone()[0]
    high_distress_count = conn.execute('''
        SELECT COUNT(DISTINCT user_id) FROM checkins 
        WHERE predicted_indicator = 'High' AND created_at >= date('now', '-7 days')
    ''').fetchone()[0]
    pending_alerts_count = conn.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Pending'").fetchone()[0]

    # Filters
    indicator_filter = request.args.get('indicator', '')
    date_filter = request.args.get('days', '14')

    query = '''
        SELECT c.*, u.anonymous_id, u.age_group 
        FROM checkins c
        JOIN users u ON c.user_id = u.id
        WHERE 1=1
    '''
    params = []

    if indicator_filter in ['Low', 'Moderate', 'High']:
        query += " AND c.predicted_indicator = ?"
        params.append(indicator_filter)

    if date_filter.isdigit():
        query += f" AND c.created_at >= date('now', '-{int(date_filter)} days')"

    query += " ORDER BY c.created_at DESC LIMIT 50"

    filtered_checkins = conn.execute(query, params).fetchall()

    # Alerts
    alerts = conn.execute('''
        SELECT a.*, u.anonymous_id, u.age_group
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC LIMIT 10
    ''').fetchall()

    # Followups
    followups = conn.execute('''
        SELECT f.*, u.anonymous_id, c.name as counselor_name
        FROM followups f
        JOIN users u ON f.user_id = u.id
        JOIN users c ON f.counselor_id = c.id
        ORDER BY f.created_at DESC LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template('counselor_dashboard.html',
                           total_survivors=total_survivors,
                           recent_checkins_count=recent_checkins_count,
                           high_distress_count=high_distress_count,
                           pending_alerts_count=pending_alerts_count,
                           checkins=filtered_checkins,
                           alerts=alerts,
                           followups=followups,
                           indicator_filter=indicator_filter,
                           date_filter=date_filter)

@app.route('/counselor/users')
@login_required
@role_required('counselor', 'admin')
def counselor_users():
    conn = get_db_connection()
    survivors = conn.execute('''
        SELECT u.id, u.anonymous_id, u.age_group, u.gender_optional, u.created_at,
               (SELECT predicted_indicator FROM checkins WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) as latest_indicator,
               (SELECT created_at FROM checkins WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) as last_checkin,
               (SELECT COUNT(*) FROM checkins WHERE user_id = u.id) as total_checkins
        FROM users u
        WHERE u.role = 'survivor'
        ORDER BY last_checkin DESC
    ''').fetchall()
    conn.close()

    return render_template('counselor_users.html', survivors=survivors)

@app.route('/counselor/alerts', methods=['GET', 'POST'])
@login_required
@role_required('counselor', 'admin')
def counselor_alerts():
    conn = get_db_connection()

    if request.method == 'POST':
        alert_id = request.form.get('alert_id')
        new_status = request.form.get('status')
        note_text = request.form.get('notes', '').strip()

        if alert_id and new_status:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET status = ? WHERE id = ?", (new_status, alert_id))
            
            # Fetch user_id for this alert to create optional followup note
            alert_obj = conn.execute("SELECT user_id FROM alerts WHERE id = ?", (alert_id,)).fetchone()
            if alert_obj and note_text:
                cursor.execute('''
                    INSERT INTO followups (user_id, counselor_id, notes, status)
                    VALUES (?, ?, ?, ?)
                ''', (alert_obj['user_id'], session['user_id'], note_text, new_status))
            
            conn.commit()
            flash("Alert status updated successfully.", "success")

    alerts = conn.execute('''
        SELECT a.*, u.anonymous_id, u.age_group
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
    ''').fetchall()
    conn.close()

    return render_template('alerts.html', alerts=alerts)

# ==========================================
# ADMIN ROUTES
# ==========================================

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    conn = get_db_connection()

    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_survivors = conn.execute("SELECT COUNT(*) FROM users WHERE role='survivor'").fetchone()[0]
    total_counselors = conn.execute("SELECT COUNT(*) FROM users WHERE role='counselor'").fetchone()[0]
    total_checkins = conn.execute("SELECT COUNT(*) FROM checkins").fetchone()[0]

    counselors_list = conn.execute("SELECT id, name, email, created_at FROM users WHERE role='counselor'").fetchall()
    resources_list = conn.execute("SELECT * FROM support_resources ORDER BY id DESC").fetchall()

    conn.close()

    metrics = get_model_metrics()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_survivors=total_survivors,
                           total_counselors=total_counselors,
                           total_checkins=total_checkins,
                           counselors=counselors_list,
                           resources=resources_list,
                           metrics=metrics)

@app.route('/admin/counselors/add', methods=['POST'])
@login_required
@role_required('admin')
def add_counselor():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash("All counselor fields are required.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        flash("User email already exists.", "danger")
        return redirect(url_for('admin_dashboard'))

    anon_id = f"COUNS-{request.form.get('badge_id', '999')}"
    pwd_hash = hash_password(password)

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (anonymous_id, name, email, age_group, password_hash, role)
        VALUES (?, ?, ?, 'Staff', ?, 'counselor')
    ''', (anon_id, name, email, pwd_hash))
    conn.commit()
    conn.close()

    flash(f"Authorized counselor account created for {name}.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/resources/add', methods=['POST'])
@login_required
@role_required('admin')
def add_resource():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    contact = request.form.get('contact', '').strip()
    location = request.form.get('location', '').strip()
    category = request.form.get('category', 'Helpline')

    if not name or not contact:
        flash("Resource name and contact information are required.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO support_resources (name, description, contact, location, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, contact, location, category))
    conn.commit()
    conn.close()

    flash(f"Support resource '{name}' added successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/resources/delete/<int:resource_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_resource(resource_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM support_resources WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()

    flash("Support resource deleted.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/model/retrain', methods=['POST'])
@login_required
@role_required('admin')
def retrain_model():
    metrics = train_and_save_model()
    flash(f"ML Model successfully retrained on synthetic dataset! New Accuracy: {metrics['accuracy']*100:.1f}%.", "success")
    return redirect(url_for('admin_dashboard'))

# ==========================================
# API ENDPOINTS FOR CHARTS
# ==========================================

@app.route('/api/survivor/trends')
@login_required
@role_required('survivor')
def api_survivor_trends():
    user_id = session['user_id']
    conn = get_db_connection()
    checkins = conn.execute('''
        SELECT stress_score, sleep_score, concentration_score, social_support_score, distress_frequency, predicted_indicator, strftime('%m/%d', created_at) as date_label
        FROM checkins
        WHERE user_id = ?
        ORDER BY created_at ASC
        LIMIT 14
    ''', (user_id,)).fetchall()
    conn.close()

    data = {
        'labels': [c['date_label'] for c in checkins],
        'stress': [c['stress_score'] for c in checkins],
        'sleep': [c['sleep_score'] for c in checkins],
        'concentration': [c['concentration_score'] for c in checkins],
        'support': [c['social_support_score'] for c in checkins],
        'distress_freq': [c['distress_frequency'] for c in checkins],
        'indicators': [c['predicted_indicator'] for c in checkins]
    }
    return jsonify(data)

@app.route('/api/counselor/distress_distribution')
@login_required
@role_required('counselor', 'admin')
def api_distress_distribution():
    conn = get_db_connection()
    counts = conn.execute('''
        SELECT predicted_indicator, COUNT(*) as count 
        FROM checkins 
        GROUP BY predicted_indicator
    ''').fetchall()
    conn.close()

    dist_map = {'Low': 0, 'Moderate': 0, 'High': 0}
    for row in counts:
        if row['predicted_indicator'] in dist_map:
            dist_map[row['predicted_indicator']] = row['count']

    return jsonify(dist_map)

# ==========================================
# REAL-TIME COUNSELOR ALERT API
# ==========================================

@app.route('/api/counselor/live_alerts')
@login_required
@role_required('counselor', 'admin')
def api_counselor_live_alerts():
    """
    Returns live metrics and recent pending High-distress alerts for real-time notification.
    Ensures zero PII exposure (only anonymous_id, indicator, timestamp, reason).
    """
    conn = get_db_connection()

    # Counts
    pending_alerts_count = conn.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Pending'").fetchone()[0]
    high_distress_count = conn.execute('''
        SELECT COUNT(DISTINCT user_id) FROM checkins 
        WHERE predicted_indicator = 'High' AND created_at >= date('now', '-7 days')
    ''').fetchone()[0]
    recent_checkins_count = conn.execute("SELECT COUNT(*) FROM checkins WHERE created_at >= date('now', '-7 days')").fetchone()[0]
    total_survivors = conn.execute("SELECT COUNT(*) FROM users WHERE role='survivor'").fetchone()[0]

    # Latest unhandled High-distress alert
    latest_high_alert_row = conn.execute('''
        SELECT a.id, a.user_id, a.indicator, a.reason, a.status, a.created_at,
               u.anonymous_id, u.age_group
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        WHERE a.indicator = 'High' AND a.status = 'Pending'
        ORDER BY a.created_at DESC, a.id DESC
        LIMIT 1
    ''').fetchone()

    latest_high_alert = None
    if latest_high_alert_row:
        latest_high_alert = {
            'id': latest_high_alert_row['id'],
            'anonymous_id': latest_high_alert_row['anonymous_id'],
            'indicator': latest_high_alert_row['indicator'],
            'reason': latest_high_alert_row['reason'],
            'status': latest_high_alert_row['status'],
            'created_at': latest_high_alert_row['created_at'],
            'message': 'High Distress Alert: A survivor’s recent responses indicate elevated distress. Please review and consider follow-up.'
        }

    # Top 4 most recent alerts for updating the dashboard preview table dynamically
    recent_alerts_rows = conn.execute('''
        SELECT a.id, a.indicator, a.reason, a.status, a.created_at, u.anonymous_id
        FROM alerts a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC, a.id DESC
        LIMIT 4
    ''').fetchall()

    recent_alerts = []
    for r in recent_alerts_rows:
        recent_alerts.append({
            'id': r['id'],
            'anonymous_id': r['anonymous_id'],
            'indicator': r['indicator'],
            'reason': r['reason'],
            'status': r['status'],
            'created_at': r['created_at']
        })

    conn.close()

    return jsonify({
        'has_high_alert': bool(latest_high_alert),
        'high_alert': latest_high_alert,
        'pending_alerts_count': pending_alerts_count,
        'high_distress_count': high_distress_count,
        'recent_checkins_count': recent_checkins_count,
        'total_survivors': total_survivors,
        'recent_alerts': recent_alerts
    })

@app.route('/api/counselor/dismiss_alert', methods=['POST'])
@login_required
@role_required('counselor', 'admin')
def api_dismiss_alert():
    """Dismisses an alert so it no longer interrupts the counselor."""
    data = request.get_json(silent=True) or request.form
    alert_id = data.get('alert_id')
    if not alert_id:
        return jsonify({'error': 'alert_id is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = 'Dismissed' WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Alert dismissed.'})

@app.route('/api/counselor/review_alert', methods=['POST'])
@login_required
@role_required('counselor', 'admin')
def api_review_alert():
    """Marks an alert as 'In Review'."""
    data = request.get_json(silent=True) or request.form
    alert_id = data.get('alert_id')
    if not alert_id:
        return jsonify({'error': 'alert_id is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = 'In Review' WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Alert marked In Review.'})

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting carebridge application on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
