import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

def generate_synthetic_data(num_samples=1500, random_seed=42):
    np.random.seed(random_seed)
    
    # Generate realistic check-in feature values (1 to 10 scale)
    stress_score = np.random.randint(1, 11, size=num_samples)
    sleep_score = np.random.randint(1, 11, size=num_samples)
    concentration_score = np.random.randint(1, 11, size=num_samples)
    social_support_score = np.random.randint(1, 11, size=num_samples)
    distress_frequency = np.random.randint(1, 11, size=num_samples)
    previous_checkin_score = np.round(np.random.uniform(1.0, 10.0, size=num_samples), 1)

    # Risk score calculation formula with slight noise for realism
    # High stress, high distress frequency, low sleep, low concentration, low support raise distress level
    risk_raw = (
        stress_score * 1.5 +
        (11 - sleep_score) * 1.2 +
        (11 - concentration_score) * 1.0 +
        (11 - social_support_score) * 1.1 +
        distress_frequency * 1.4 +
        previous_checkin_score * 0.8 +
        np.random.normal(0, 2.0, size=num_samples)
    )

    # Categorize into Low, Moderate, High
    # 0: Low, 1: Moderate, 2: High
    labels = []
    for score in risk_raw:
        if score < 28.0:
            labels.append('Low')
        elif score < 42.0:
            labels.append('Moderate')
        else:
            labels.append('High')

    df = pd.DataFrame({
        'stress_score': stress_score,
        'sleep_score': sleep_score,
        'concentration_score': concentration_score,
        'social_support_score': social_support_score,
        'distress_frequency': distress_frequency,
        'previous_checkin_score': previous_checkin_score,
        'distress_indicator': labels
    })

    return df

def train_and_save_model(base_dir=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    df = generate_synthetic_data()
    csv_path = os.path.join(data_dir, 'synthetic_dataset.csv')
    df.to_csv(csv_path, index=False)
    print(f"Synthetic dataset saved to {csv_path}")

    X = df[['stress_score', 'sleep_score', 'concentration_score', 'social_support_score', 'distress_frequency', 'previous_checkin_score']]
    y = df['distress_indicator']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Train an interpretable Decision Tree Classifier
    clf = DecisionTreeClassifier(max_depth=5, min_samples_split=10, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average='weighted'))
    rec = float(recall_score(y_test, y_pred, average='weighted'))
    labels_order = ['Low', 'Moderate', 'High']
    cm = confusion_matrix(y_test, y_pred, labels=labels_order).tolist()

    feature_importances = dict(zip(X.columns, [round(float(imp), 4) for imp in clf.feature_importances_]))

    metrics = {
        'model_type': 'DecisionTreeClassifier',
        'max_depth': 5,
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'labels': labels_order,
        'confusion_matrix': cm,
        'feature_importances': feature_importances,
        'sample_count': len(df)
    }

    model_path = os.path.join(models_dir, 'distress_model.pkl')
    metrics_path = os.path.join(models_dir, 'model_metrics.json')

    joblib.dump(clf, model_path)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)

    print(f"Model saved to {model_path}")
    print(f"Metrics saved to {metrics_path}")
    print(f"Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}")
    return metrics

if __name__ == '__main__':
    train_and_save_model()
