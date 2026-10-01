import os
import json
import joblib
import pandas as pd
import numpy as np
from utils.database import get_db_connection

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'distress_model.pkl')
METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'model_metrics.json')

_model = None

def get_model():
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        print("Model file not found. Running training script...")
        from models.train_model import train_and_save_model
        train_and_save_model()

    try:
        _model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        _model = None
    return _model

def get_model_metrics():
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def calculate_previous_checkin_score(user_id):
    conn = get_db_connection()
    recent = conn.execute('''
        SELECT stress_score, sleep_score, concentration_score, social_support_score, distress_frequency
        FROM checkins
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 3
    ''', (user_id,)).fetchall()
    conn.close()

    if not recent:
        return 5.0 # default neutral baseline

    avg_scores = []
    for r in recent:
        # compute composite composite score (1 to 10 scale)
        composite = (r['stress_score'] + (11 - r['sleep_score']) + (11 - r['concentration_score']) + (11 - r['social_support_score']) + r['distress_frequency']) / 5.0
        avg_scores.append(composite)

    return round(float(np.mean(avg_scores)), 1)

def analyze_contributing_factors(stress, sleep, concentration, support, distress_freq):
    factors = []
    if stress >= 7:
        factors.append(f"You reported carrying heavy stress right now ({stress}/10).")
    elif stress >= 5:
        factors.append(f"You mentioned feeling a noticeable amount of daily stress ({stress}/10).")

    if sleep <= 4:
        factors.append(f"Your rest was interrupted or difficult last night ({sleep}/10 sleep quality).")

    if concentration <= 4:
        factors.append(f"It felt unusually hard to keep your focus today ({concentration}/10).")

    if support <= 4:
        factors.append(f"You felt somewhat on your own today ({support}/10 support score). Connecting with someone you trust may help.")

    if distress_freq >= 7:
        factors.append(f"Difficult or distressing thoughts visited you frequently today ({distress_freq}/10).")

    if not factors:
        factors.append("Your responses today reflect a steady, balanced emotional baseline.")

    return factors

def get_suggested_next_step(indicator):
    if indicator == 'High':
        return {
            'action': 'Reach Out to a Friendly Voice or Support Guide',
            'details': 'Today feels heavy and overwhelming, and you do not have to carry it alone. Please consider talking to a trusted friend, counselor, or care worker who can listen and support you.',
            'alert_level': 'danger'
        }
    elif indicator == 'Moderate':
        return {
            'action': 'Take a Gentle Pause and Reconnect',
            'details': 'You are navigating some noticeable tension today. Try taking a quiet breath, stepping away for a short walk, or sharing a quick message with someone supportive.',
            'alert_level': 'warning'
        }
    else:
        return {
            'action': 'Keep Nurturing Your Everyday Rhythm',
            'details': 'You are in a calm and steady space today. Continuing your daily check-in routine helps celebrate small victories and preserve peace of mind.',
            'alert_level': 'success'
        }

def predict_distress_indicator(stress, sleep, concentration, support, distress_freq, prev_score=5.0):
    model = get_model()
    
    features = pd.DataFrame([{
        'stress_score': int(stress),
        'sleep_score': int(sleep),
        'concentration_score': int(concentration),
        'social_support_score': int(support),
        'distress_frequency': int(distress_freq),
        'previous_checkin_score': float(prev_score)
    }])

    if model is not None:
        try:
            pred = model.predict(features)[0]
            if hasattr(model, 'predict_proba'):
                probas = model.predict_proba(features)[0]
                conf = float(np.max(probas))
            else:
                conf = 0.85
        except Exception as e:
            print(f"Prediction error, falling back to heuristic: {e}")
            pred, conf = fallback_heuristic_prediction(stress, sleep, concentration, support, distress_freq)
    else:
        pred, conf = fallback_heuristic_prediction(stress, sleep, concentration, support, distress_freq)

    factors = analyze_contributing_factors(stress, sleep, concentration, support, distress_freq)
    next_step = get_suggested_next_step(pred)

    return {
        'indicator': pred,
        'confidence': round(conf, 2),
        'factors': factors,
        'next_step': next_step
    }

def fallback_heuristic_prediction(stress, sleep, concentration, support, distress_freq):
    comp = stress * 1.5 + (11 - sleep) * 1.2 + (11 - concentration) * 1.0 + (11 - support) * 1.1 + distress_freq * 1.4
    if comp >= 38:
        return 'High', 0.88
    elif comp >= 26:
        return 'Moderate', 0.82
    else:
        return 'Low', 0.90

def evaluate_early_warning_rules(user_id, current_checkin):
    """
    Evaluates rule-based early warning thresholds for survivors.
    Creates supportive, non-diagnostic alerts if thresholds are exceeded
    or if the AI distress indicator is High.
    """
    conn = get_db_connection()
    past_checkins = conn.execute('''
        SELECT stress_score, sleep_score, predicted_indicator, created_at
        FROM checkins
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    reasons = []

    # Rule 0: Current check-in flagged with High distress indicator
    is_high_distress = (current_checkin.get('predicted_indicator') == 'High')
    if is_high_distress:
        reasons.append("Recent self-reflection indicates elevated distress levels")

    if len(past_checkins) >= 2:
        # Rule 1: Sudden increase in stress level (+4 or more)
        recent_stress = [c['stress_score'] for c in past_checkins]
        if len(recent_stress) >= 2 and (recent_stress[0] - recent_stress[1] >= 4):
            reasons.append(f"Notable rise in daily stress (+{recent_stress[0] - recent_stress[1]} points) since the last check-in")

        # Rule 2: Repeated poor sleep scores (sleep <= 3 for last 3 check-ins)
        recent_sleep = [c['sleep_score'] for c in past_checkins[:3]]
        if len(recent_sleep) >= 3 and all(s <= 3 for s in recent_sleep):
            reasons.append("Restless or poor sleep quality reported over the last 3 check-ins")

        # Rule 3: Multiple consecutive high distress indicators
        recent_indicators = [c['predicted_indicator'] for c in past_checkins[:2]]
        if len(recent_indicators) >= 2 and all(ind == 'High' for ind in recent_indicators):
            reasons.append("Consecutive elevated distress indicators observed")

    alert_created = None
    if reasons:
        alert_reason = "; ".join(reasons)
        indicator_level = 'High' if is_high_distress or len(reasons) > 1 else 'Moderate'

        # Check if an unresolved alert already exists today for this user
        existing = conn.execute('''
            SELECT id FROM alerts 
            WHERE user_id = ? AND status = 'Pending' AND created_at >= date('now')
        ''', (user_id,)).fetchone()

        if not existing:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (user_id, indicator, reason, status)
                VALUES (?, ?, ?, 'Pending')
            ''', (user_id, indicator_level, f"Supportive follow-up suggested: {alert_reason}"))
            conn.commit()
            alert_created = alert_reason

    conn.close()
    return alert_created
