import os
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

def get_db_path():
    if os.environ.get('DATABASE_PATH'):
        return os.environ.get('DATABASE_PATH')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, 'database')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anonymous_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age_group TEXT NOT NULL,
            gender_optional TEXT,
            contact_pref TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'survivor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create checkins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stress_score INTEGER NOT NULL,
            sleep_score INTEGER NOT NULL,
            concentration_score INTEGER NOT NULL,
            social_support_score INTEGER NOT NULL,
            distress_frequency INTEGER NOT NULL,
            previous_checkin_score REAL,
            predicted_indicator TEXT NOT NULL,
            predicted_probability REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            indicator TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Create followups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            counselor_id INTEGER NOT NULL,
            notes TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (counselor_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Create support_resources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Helpline',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create system_config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

def seed_demo_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        print("Demo data already seeded.")
        return

    print("Seeding synthetic demo data...")

    # Hashed default password
    pwd_hash = generate_password_hash("password123")
    admin_pwd_hash = generate_password_hash("admin123")
    counselor_pwd_hash = generate_password_hash("counselor123")

    # 1. Users
    users_data = [
        ('ADMIN-001', 'System Administrator', 'admin@carebridge.org', '35-49', 'Prefer not to say', 'Email', admin_pwd_hash, 'admin'),
        ('COUNS-101', 'Dr. Sarah Jenkins', 'counselor@carebridge.org', '35-49', 'Female', 'Phone', counselor_pwd_hash, 'counselor'),
        ('COUNS-102', 'Alex Rivera, MSW', 'support_worker@carebridge.org', '25-34', 'Non-binary', 'Email', counselor_pwd_hash, 'counselor'),
        ('CB-7842', 'User Alpha (DEMO)', 'survivor1@carebridge.org', '25-34', 'Female', 'App Notification', pwd_hash, 'survivor'),
        ('CB-9103', 'User Beta (DEMO)', 'survivor2@carebridge.org', '18-24', 'Male', 'None', pwd_hash, 'survivor'),
        ('CB-3419', 'User Gamma (DEMO)', 'survivor3@carebridge.org', '35-49', 'Other', 'SMS', pwd_hash, 'survivor')
    ]

    cursor.executemany('''
        INSERT INTO users (anonymous_id, name, email, age_group, gender_optional, contact_pref, password_hash, role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', users_data)

    conn.commit()

    # Fetch user IDs
    cursor.execute("SELECT id, anonymous_id, email FROM users WHERE role='survivor'")
    survivors = cursor.fetchall()
    survivor_map = {s['email']: s['id'] for s in survivors}
    
    cursor.execute("SELECT id FROM users WHERE role='counselor'")
    counselor_id = cursor.fetchone()['id']

    # 2. Support Resources (Clearly marked synthetic / placeholder)
    resources_data = [
        ("National Crisis Support Line", "24/7 confidential crisis support helpline for immediate emotional distress.", "1-800-DEMO-CARE (Placeholder)", "National / Worldwide", "Helpline"),
        ("Community Healing Network", "Peer support group directory and holistic wellness resources for trauma survivors.", "support@demo-healing.org (Placeholder)", "Regional", "NGO"),
        ("Trauma-Informed Counseling Collective", "Free and subsidized professional therapy sessions with accredited counseling staff.", "contact@demo-therapy.org (Placeholder)", "Urban Metro Area", "Medical"),
        ("International Resettlement & Wellness Desk", "Support services for displaced individuals and families affected by crisis.", "desk@demo-resettlement.org (Placeholder)", "Global", "Crisis Center")
    ]

    cursor.executemany('''
        INSERT INTO support_resources (name, description, contact, location, category)
        VALUES (?, ?, ?, ?, ?)
    ''', resources_data)

    # 3. Check-ins history over past 14 days
    now = datetime.now()
    checkin_samples = []
    
    # Survivor 1 (CB-7842) - Rising distress trend
    s1_id = survivor_map['survivor1@carebridge.org']
    for day in range(14, -1, -1):
        dt = (now - timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
        # Stress increases over time
        stress = min(10, max(2, 3 + (14 - day) // 2 + random.randint(-1, 1)))
        sleep = max(1, min(10, 8 - (14 - day) // 2 + random.randint(-1, 1)))
        conc = max(1, min(10, 7 - (14 - day) // 3 + random.randint(-1, 1)))
        supp = random.randint(5, 8)
        dist_freq = min(10, max(1, 2 + (14 - day) // 2 + random.randint(-1, 1)))
        
        # Determine indicator
        score_val = stress * 1.5 + (11 - sleep) * 1.2 + (11 - conc) * 1.0 + (11 - supp) * 1.1 + dist_freq * 1.4
        if score_val >= 38:
            ind = 'High'
        elif score_val >= 26:
            ind = 'Moderate'
        else:
            ind = 'Low'

        checkin_samples.append((s1_id, stress, sleep, conc, supp, dist_freq, round(score_val/5, 1), ind, 0.85, dt))

    # Survivor 2 (CB-9103) - Stable low/moderate distress
    s2_id = survivor_map['survivor2@carebridge.org']
    for day in range(10, -1, -2):
        dt = (now - timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
        stress = random.randint(2, 4)
        sleep = random.randint(6, 9)
        conc = random.randint(6, 8)
        supp = random.randint(7, 9)
        dist_freq = random.randint(1, 3)
        ind = 'Low'
        checkin_samples.append((s2_id, stress, sleep, conc, supp, dist_freq, 3.2, ind, 0.92, dt))

    # Survivor 3 (CB-3419) - High distress pattern
    s3_id = survivor_map['survivor3@carebridge.org']
    for day in range(7, -1, -1):
        dt = (now - timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
        stress = random.randint(8, 10)
        sleep = random.randint(1, 3)
        conc = random.randint(2, 4)
        supp = random.randint(2, 4)
        dist_freq = random.randint(7, 10)
        ind = 'High'
        checkin_samples.append((s3_id, stress, sleep, conc, supp, dist_freq, 8.5, ind, 0.94, dt))

    cursor.executemany('''
        INSERT INTO checkins (user_id, stress_score, sleep_score, concentration_score, social_support_score, distress_frequency, previous_checkin_score, predicted_indicator, predicted_probability, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', checkin_samples)

    # 4. Initial Alerts
    alerts_data = [
        (s1_id, 'High', 'Sudden increase in stress level (+4 points) over recent 3 check-ins.', 'Pending', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
        (s3_id, 'High', 'Multiple consecutive high distress indicators reported (3 days in a row).', 'Pending', now.strftime('%Y-%m-%d %H:%M:%S'))
    ]

    cursor.executemany('''
        INSERT INTO alerts (user_id, indicator, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', alerts_data)

    # 5. Initial Followups
    followups_data = [
        (s1_id, counselor_id, 'Scheduled proactive check-in call with support worker regarding sleep quality trend.', 'Scheduled', (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'))
    ]

    cursor.executemany('''
        INSERT INTO followups (user_id, counselor_id, notes, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', followups_data)

    conn.commit()
    conn.close()
    print("Synthetic demo data seeded successfully.")
