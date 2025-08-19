# Trains Model B (text/sentiment-based) using VADER + RandomForest.
# Reads `datasets/model_b_train.csv`, computes sentiment, trains the model,
# writes predictions to `datasets/model_b_predictions.csv`, and saves the model.
# Uses ASCII-only console logs for Windows compatibility (no emojis).
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import resample
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import joblib

# 📦 Download VADER lexicon if not already present
nltk.download('vader_lexicon')

# === Paths ===
DATASET_PATH = 'datasets/model_b_train.csv'
SENTIMENT_PATH = 'datasets/sentiment_analysis.csv'
PREDICTIONS_PATH = 'datasets/model_b_predictions.csv'
MODEL_PATH = 'models/model_b_latest.pkl'
os.makedirs('models', exist_ok=True)

# === Load data ===
print(f"[INFO] Loading dataset from: {DATASET_PATH}")
df = pd.read_csv(DATASET_PATH)
df['review'] = df['review'].fillna("").astype(str)

# === Apply VADER sentiment ===
print("[INFO] Applying VADER sentiment analysis...")
sia = SentimentIntensityAnalyzer()
df['compound_score'] = df['review'].apply(lambda x: sia.polarity_scores(x)['compound'])

# Save sentiment scores
sentiment_df = df[['userid', 'review', 'compound_score']]
sentiment_df.to_csv(SENTIMENT_PATH, index=False)
print(f"[OK] Sentiment scores saved to: {SENTIMENT_PATH}")

# === Prepare features ===
X = df[['compound_score']]
y = df['is_churned']
uids = df['userid']

# === Train/test split ===
X_train, X_test, y_train, y_test, uid_train, uid_test = train_test_split(
    X, y, uids, test_size=0.3, random_state=42, stratify=y
)

# === Stratified Undersampling on training data only ===
train_df = pd.DataFrame({'compound_score': X_train['compound_score'], 'is_churned': y_train})
minority = train_df[train_df['is_churned'] == 0]
majority = train_df[train_df['is_churned'] == 1]

if len(majority) > len(minority):
    majority_downsampled = resample(
        majority,
        replace=False,
        n_samples=len(minority),
        random_state=42
    )
    train_balanced = pd.concat([majority_downsampled, minority])
else:
    train_balanced = train_df

X_train_bal = train_balanced[['compound_score']]
y_train_bal = train_balanced['is_churned']

# === Train Random Forest ===
print("[INFO] Training Random Forest...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_bal, y_train_bal)

# === Evaluation ===
print("\n[INFO] Evaluation on test set:")
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# === Save predictions with churn probability & risk ===
y_proba = model.predict_proba(X)[:, 1]
churn_prob_pct = np.round(y_proba * 100, 2)

def get_risk(prob):
    return "High" if prob >= 70 else "Medium" if prob >= 40 else "Low"

pred_df = pd.DataFrame({
    'userid': uids,
    'churn_probability (%)': churn_prob_pct,
    'churn_risk': [get_risk(p) for p in churn_prob_pct],

})

pred_df.to_csv(PREDICTIONS_PATH, index=False)
print(f"\n[OK] Predictions saved to: {PREDICTIONS_PATH}")

# === Save model ===
joblib.dump(model, MODEL_PATH)
print(f"[OK] Random Forest model saved to: {MODEL_PATH}")
