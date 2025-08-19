import pandas as pd
import json
import os

# Load model predictions
df_a = pd.read_csv('datasets/model_a_predictions.csv')
df_b = pd.read_csv('datasets/model_b_predictions.csv')

# Load top features for each user
try:
    with open('models/user_top_features.json', 'r') as f:
        user_features = {str(item['userid']): item['top_features'] for item in json.load(f)}
except FileNotFoundError:
    print("[WARN] User features not found. Run train_model_a.py first.")
    user_features = {}

# Rename columns
df_a.rename(columns={'churn_probability': 'a_prob'}, inplace=True)
df_b.rename(columns={'churn_probability (%)': 'b_prob'}, inplace=True)

# Merge A and B on userid
combined = pd.merge(df_a, df_b[['userid', 'b_prob']], on='userid', how='left')

# Fill final probability: average if both exist, else just A
def calculate_final(row):
    if pd.notna(row['b_prob']):
        return (row['a_prob'] + row['b_prob']) / 2
    return row['a_prob']

combined['churn_probability (%)'] = combined.apply(calculate_final, axis=1)

# Risk level logic
def get_risk(prob):
    if prob >= 80:
        return 'High'
    elif prob >= 50:
        return 'Medium'
    else:
        return 'Low'

combined['churn_risk'] = combined['churn_probability (%)'].apply(get_risk)

# Add top features to the output
combined['top_factors'] = combined['userid'].astype(str).map(
    lambda x: json.dumps(user_features.get(x, []))
)

# Final output with all data
final = combined[['userid', 'churn_probability (%)', 'churn_risk', 'top_factors']]
final.to_csv('datasets/churn_prediction.csv', index=False)
print("[OK] Final churn_prediction.csv generated with top factors.")
