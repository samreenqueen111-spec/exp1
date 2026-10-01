# CareBridge 🌿
### AI-Powered Dynamic Mental Health Monitoring & Distress Prediction System for Victims of Atrocities

> **IMPORTANT DISCLAIMER:** CareBridge is an academic and hackathon prototype designed for privacy-focused mental health distress monitoring. It provides **supportive risk indicators** and is **NOT a clinical medical diagnostic tool**. It does not make medical claims or replace professional healthcare providers.

---

## 📌 Project Overview & Problem Statement

Survivors of atrocities, mass displacement, or extreme traumatic events often experience severe psychological distress. Traditional mental health monitoring relies on sporadic clinical sessions, making it challenging for counselors and support workers to detect subtle downward trends or sudden spikes in distress between visits. Furthermore, survivors are often re-traumatized when forced to repeatedly recount graphic details of past events.

**CareBridge** addresses these challenges by offering a trauma-informed, privacy-first web application. Survivors complete simple, 1-to-10 numerical daily check-ins without recounting traumatic narratives. An interpretable Machine Learning (DecisionTree Classifier) combined with rule-based heuristics evaluates distress indicators, generates trend visualizations, and triggers non-diagnostic early-warning alerts for authorized caseworkers.

---

## ✨ Key Features

1. **Empathetic Landing Page (`/`)**
   - Clear explanation of platform purpose, "How It Works", privacy assurances, and emergency disclaimers.
   - Non-alarmist, professional aesthetic designed to minimize user anxiety.

2. **Pseudonymous Survivor Authentication (`/register`, `/login`)**
   - Collects minimal required information (Name/Alias, Email, Age Group, Password).
   - Generates an **Anonymous ID** (e.g., `CB-7842`) to shield personal identity in counselor views.
   - Secure password hashing using PBKDF2/SHA-256 and session-based authentication.

3. **Daily Well-Being Check-in (`/survivor/checkin`)**
   - 5-question numerical questionnaire evaluating:
     - Stress Level (1-10)
     - Sleep Quality (1-10)
     - Concentration Difficulty (1-10)
     - Social Support Feeling (1-10)
     - Distressing Thought Frequency (1-10)
   - Interactive HTML5 range sliders with live numeric value displays.

4. **Distress Risk Analysis & Guidance (`/survivor/checkin/result/<id>`)**
   - Classifies risk level into **Low**, **Moderate**, or **High** distress indicators.
   - Highlights specific contributing factors (e.g. "Elevated stress intensity reported", "Restricted sleep quality").
   - Provides supportive next steps with calm, non-diagnostic phrasing.

5. **AI/ML Module (`models/train_model.py`)**
   - Trains an interpretable **Decision Tree Classifier** on a synthetic dataset (`data/synthetic_dataset.csv`).
   - Feature Matrix: `stress_score`, `sleep_score`, `concentration_score`, `social_support_score`, `distress_frequency`, `previous_checkin_score`.
   - Evaluates performance metrics (Accuracy, Precision, Recall, Confusion Matrix) saved to `models/model_metrics.json`.

6. **Dynamic Trend Monitoring (`/survivor/dashboard`)**
   - Visualizes multi-day trends for stress, sleep, and social support using **Chart.js**.
   - Focuses on longitudinal patterns rather than reacting to isolated single-day responses.

7. **Authorized Counselor Portal (`/counselor/dashboard`, `/counselor/users`)**
   - Anonymized view displaying only pseudonymous Anonymous IDs, age groups, and risk levels.
   - Filterable check-in table by date range and risk level.
   - Roster view with last check-in timestamps and follow-up status.

8. **Rule + ML Early-Warning System (`/counselor/alerts`)**
   - Evaluates thresholds such as sudden stress jumps (≥ +4 points), repeated poor sleep (sleep ≤ 3 for 3 consecutive days), and consecutive high distress indicators.
   - Triggers non-diagnostic alerts ("Follow-up recommended based on recent response patterns").
   - Counselor interface for status tracking (`Pending`, `In Review`, `Resolved`) and logging notes.

9. **Dedicated Support Resources (`/survivor/support`)**
   - Categorized directory of crisis helplines, NGOs, medical therapy networks, and resettlement desks.
   - Fully configurable by administrators.
   - Clearly marked placeholder contact details to avoid invalid numbers.

10. **Admin Control Panel (`/admin/dashboard`)**
    - Displays overall system stats, user role counts, and ML diagnostic metrics.
    - Forms to add new authorized counselors and support resources.
    - One-click synthetic model retraining button.

---

## 🛠 Tech Stack

- **Frontend:** HTML5, CSS3 (CSS Variables, Flexbox/Grid), JavaScript (ES6+), Chart.js (v4 CDN)
- **Backend:** Python 3.13, Flask, Werkzeug Security
- **Database:** SQLite (parameterized queries, zero raw SQL injection vulnerability)
- **AI/ML:** Scikit-learn (DecisionTree), Pandas, NumPy, Joblib
- **Testing:** Python `unittest` framework

---

## 📁 Project Structure

```
carebridge/
│
├── app.py                      # Flask main server & route controller
├── requirements.txt            # Dependencies manifest
├── README.md                   # System documentation
│
├── database/
│   └── database.db             # SQLite database (auto-created on startup)
│
├── models/
│   ├── train_model.py          # Synthetic dataset generator & DecisionTree training pipeline
│   ├── distress_model.pkl      # Trained Scikit-learn model artifact
│   └── model_metrics.json      # Model accuracy, precision, recall & confusion matrix
│
├── data/
│   └── synthetic_dataset.csv   # Synthetic baseline dataset (1500 samples)
│
├── templates/
│   ├── base.html               # Base layout with navbar & safety disclaimers
│   ├── index.html              # Landing page
│   ├── about.html              # About & methodology
│   ├── privacy.html            # Privacy & data safety policy
│   ├── login.html              # Login page with demo credentials helper
│   ├── register.html           # Minimal survivor registration
│   ├── survivor_dashboard.html # Survivor dashboard & Chart.js trends
│   ├── checkin.html            # Daily check-in questionnaire with range sliders
│   ├── checkin_result.html     # Check-in result breakdown & recommendations
│   ├── history.html            # Survivor check-in history table
│   ├── support.html            # Support resources directory
│   ├── counselor_dashboard.html# Counselor monitoring dashboard & filters
│   ├── counselor_users.html    # Anonymized survivor roster
│   ├── alerts.html             # Early-warning alerts desk
│   ├── admin_dashboard.html    # Admin panel & ML diagnostic metrics
│   ├── 404.html                # Custom 404 error view
│   └── 500.html                # Custom 500 error view
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom calm responsive stylesheet
│   └── js/
│       └── dashboard.js        # Interactive slider handlers & Chart.js logic
│
├── utils/
│   ├── database.py             # SQLite initialization & demo data seeder
│   ├── auth.py                 # Password hashing & session auth decorators
│   └── prediction.py           # ML inference engine & early-warning rules
│
└── tests/
    └── test_app.py             # Automated unit & integration tests
```

---

## 🔑 Demo Credentials (Hackathon Evaluators)

| Role | Identifier / Email | Password | Access Capabilities |
|---|---|---|---|
| **Survivor** | `survivor1@carebridge.org` | `password123` | Check-in submission, personal trends, history |
| **Survivor 2** | `survivor2@carebridge.org` | `password123` | Stable baseline check-in history |
| **Counselor** | `counselor@carebridge.org` | `counselor123` | Anonymized survivor roster, filters, alert updates |
| **Admin** | `admin@carebridge.org` | `admin123` | ML diagnostics, counselor provisioning, retrain model |

---

## 🚀 How to Run Locally

### 1. Clone or Download Repository
Navigate into the project folder:
```bash
cd carebridge
```

### 2. Install Required Python Packages
```bash
pip install -r requirements.txt
```

### 3. Initialize Database & Train Model (Automatic on First Run)
Simply run `app.py`. On startup, CareBridge will automatically:
- Create the SQLite database schema in `database/database.db`.
- Train the ML model and generate `models/distress_model.pkl`.
- Seed synthetic demo survivors, counselors, check-ins, alerts, and resources.

```bash
python app.py
```

### 4. Access Application
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 5. Run Automated Tests
```bash
python -m unittest discover -s tests
```

---

## 🖼 Screenshots & UI Previews

*(Placeholders for presentation slides / README assets)*
- **Landing Page Hero & Pillars:** Soft teal design with privacy assurances.
- **Interactive Check-In:** Smooth 1-10 sliders for stress, sleep, and support.
- **Survivor Trends:** Chart.js dynamic line graph tracking 14-day history.
- **Counselor Portal:** Anonymized records with risk filters and early warning alerts.
- **Admin Diagnostics:** Model accuracy, precision, recall, and confusion matrix card.

---

## 🛡 Security & Privacy Controls

- **Zero Real Victim Data:** Training and demo datasets use strictly synthetic values.
- **Pseudonymization:** Survivors are referred to by Anonymous IDs (`CB-XXXX`) in caseworker views.
- **Password Hashing:** Uses `werkzeug.security.generate_password_hash`.
- **SQL Parameterization:** Protects against SQL injection across all endpoints.
- **Role-Based Guards:** Custom Python decorators (`@login_required`, `@role_required`) enforce strict route authorization.

---

## 🔮 Future Enhancements

- **End-to-End Encryption (E2EE):** Encrypt stored check-in values at rest using client-side keys.
- **Multilingual Support:** Localize interface into Arabic, Ukrainian, Spanish, and French.
- **Offline PWA Capability:** Enable offline check-ins for low-connectivity refugee camps with background sync.
- **Granular Role Permissions:** Custom permissions for regional NGOs vs accredited clinical therapists.
