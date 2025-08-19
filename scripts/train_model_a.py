import os
import pandas as pd
import json
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from imblearn.over_sampling import SMOTE
import shap

# === Paths ===
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
DATASET_DIR = os.path.join(base_dir, 'datasets')
MODEL_DIR = os.path.join(base_dir, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# Trains Model A (tabular features) using XGBoost.
# Reads `datasets/model_a_train.csv`, balances with SMOTE, trains XGB,
# saves model and predictions. Uses ASCII-only logs for Windows consoles.
#
# This file expects the training CSV to be append-only and will not modify it.

# === Load Dataset ===
data_path = os.path.join(DATASET_DIR, 'model_a_train.csv')
print(f"[INFO] Loading dataset from: {data_path}")
df = pd.read_csv(data_path)

# === Preprocessing ===
target_column = 'is_churned'
leakage_columns = ['userid', 'left_review', 'Last Visited Minutes', 'churn_level', 'churn_risk', target_column]
X = df.drop(columns=[col for col in leakage_columns if col in df.columns], errors='ignore')
y = df[target_column]
user_ids = df['userid']

# === Train/Test Split (for evaluation only) ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# === Apply SMOTE to balance training data ===
print("\n[INFO] Applying SMOTE...")
sm = SMOTE(random_state=42)
X_train_bal, y_train_bal = sm.fit_resample(X_train, y_train)
print(f"[OK] Balanced training set: {X_train_bal.shape}")

# === Train Model ===
print("\n[INFO] Training XGBoost...")
model = XGBClassifier(
    use_label_encoder=False,
    eval_metric='logloss',
    max_depth=6,
    learning_rate=0.1,
    n_estimators=150,
    random_state=42
)
model.fit(X_train_bal, y_train_bal)

# === Evaluate on Test Set ===
y_pred_proba_test = model.predict_proba(X_test)[:, 1]
y_pred_test = (y_pred_proba_test >= 0.6).astype(int)

print("\n[INFO] Evaluation on Test Set (20%)")
print("Accuracy:", accuracy_score(y_test, y_pred_test))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred_test))
print("Classification Report:\n", classification_report(y_test, y_pred_test))

# === Save Model and Results ===
model_path = os.path.join(MODEL_DIR, 'model_a.pkl')
joblib.dump(model, model_path)

# Get feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

# Save feature importance
feature_importance.to_csv(os.path.join(MODEL_DIR, 'feature_importance.csv'), index=False)

# Get SHAP values for each user's prediction
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# Get top 3 most important features for each user
user_top_features = []
for i, user_id in enumerate(user_ids):
    # Get absolute SHAP values for this user
    user_shap = pd.DataFrame({
        'feature': X.columns,
        'shap_value': shap_values[i],
        'feature_value': X.iloc[i].values
    })
    # Get top 3 features by absolute SHAP value
    top_features = user_shap.reindex(
        user_shap['shap_value'].abs().sort_values(ascending=False).index
    ).head(3)
    
    user_top_features.append({
        'userid': user_id,
        'top_features': top_features[['feature', 'feature_value', 'shap_value']].to_dict('records')
    })

# Save top features per user
with open(os.path.join(MODEL_DIR, 'user_top_features.json'), 'w') as f:
    json.dump(user_top_features, f)

feature_path = os.path.join(MODEL_DIR, 'model_a_features.json')
with open(feature_path, "w") as f:
    json.dump(list(X.columns), f)
print(f"[OK] Feature list saved to: {feature_path}")

threshold_path = os.path.join(MODEL_DIR, 'model_a_threshold.txt')
with open(threshold_path, "w") as f:
    f.write("0.6")
print(f"[OK] Threshold saved to: {threshold_path}")

# === Predict for ALL USERS ===
def get_risk(prob):
    if prob >= 80:
        return "High"
    elif prob >= 50:
        return "Medium"
    else:
        return "Low"

y_all_proba = model.predict_proba(X)[:, 1]
all_prob_pct = (y_all_proba * 100).round(2)

predictions_all = pd.DataFrame({
    'userid': user_ids,
    'churn_probability': all_prob_pct,
})
predictions_all['churn_risk'] = predictions_all['churn_probability'].apply(get_risk)

# Save final predictions
output_path = os.path.join(DATASET_DIR, 'model_a_predictions.csv')
predictions_all.to_csv(output_path, index=False)
print(f"\n[OK] Predictions for ALL users saved to: {output_path}")
