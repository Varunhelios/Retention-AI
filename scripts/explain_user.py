# Generates per-user explanations (top SHAP features) and actionable
# recommendations. Can run for a single user (by id) or for ALL users
# using the --all flag. Outputs JSON files under `outputs/explanations/`
# and SHAP bar charts under `outputs/charts/`.
import os
import json
import joblib
import shap
import pandas as pd
import sys
import argparse

# ✅ Prevent GUI-related crashes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# === Setup Paths ===
DATASET_DIR = "datasets"
MODEL_DIR = "models"
OUTPUT_DIR = "outputs"
EXPLAIN_DIR = os.path.join(OUTPUT_DIR, "explanations")
CHART_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(EXPLAIN_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# === Load Models and Metadata ===
model_a = joblib.load(os.path.join(MODEL_DIR, "model_a_latest.pkl"))
model_b = joblib.load(os.path.join(MODEL_DIR, "model_b_latest.pkl"))
with open(os.path.join(MODEL_DIR, "model_a_features.json")) as f:
    features_a = json.load(f)

explainer_a = shap.TreeExplainer(model_a)
explainer_b = shap.TreeExplainer(model_b)

# === Load Datasets ===
df_a = pd.read_csv(os.path.join(DATASET_DIR, "model_a_train.csv"))
df_b = pd.read_csv(os.path.join(DATASET_DIR, "model_b_train.csv"))
sentiment_df = pd.read_csv(os.path.join(DATASET_DIR, "sentiment_analysis.csv"))
df_churn = pd.read_csv(os.path.join(DATASET_DIR, "churn_prediction.csv"))

def build_recommendations(row: dict) -> list:
    """Rule-based recommendations using usage patterns, ratings, sentiment, and churn flags."""
    recs: list[str] = []

    # Usage drop / churn behavior
    drop_in = float(row.get("drop_in_usage", 0) or 0)
    is_churned = int(row.get("is_churned", 0) or 0)
    total_days_active = int(row.get("total_days_active", 0) or 0)
    avg_screen = float(row.get("Average Screen Time", 0) or 0)
    ratings = float(row.get("Ratings", 0) or 0)
    last_visited = float(row.get("Last Visited Minutes", 0) or 0)

    sentiment = row.get("compound_score")

    if is_churned == 1 or total_days_active == 0:
        recs.append("Win-back campaign: offer a limited-time incentive and a quick 2-click reactivation.")
    if drop_in >= 40:
        recs.append("Re-engage with a personalized check-in and highlight new features they missed.")
    if avg_screen > 240:
        recs.append("Encourage healthier usage with screen-break reminders and wellness tips.")
    if ratings and ratings <= 2:
        recs.append("Apologize and offer priority support to address low satisfaction.")
    elif ratings and ratings <= 3:
        recs.append("Ask for quick feedback and provide a small perk to improve experience.")
    if last_visited > 7 * 24 * 60:  # more than ~7 days in minutes
        recs.append("Send a 'we miss you' nudge with a simple return path.")

    if pd.notna(sentiment):
        s = float(sentiment)
        if s < -0.2:
            recs.append("Reach out with empathetic support to address dissatisfaction.")
        elif -0.2 <= s <= 0.2:
            recs.append("Invite feedback via a 1-question survey to understand needs.")
        elif 0.2 < s <= 0.5:
            recs.append("Thank them and suggest premium/value features they might like.")
        elif s > 0.5:
            recs.append("Ask for a public review or referrals; offer referral credits.")

    # Always include a discovery prompt
    recs.append("Offer smart tips to help users explore underused features.")

    # Deduplicate and cap to 5
    deduped: list[str] = []
    for r in recs:
        if r not in deduped:
            deduped.append(r)
        if len(deduped) == 5:
            break
    return deduped


def generate_for_user(user_id: int) -> None:
    row_a = df_a[df_a["userid"] == user_id]
    row_b = df_b[df_b["userid"] == user_id]
    sentiment = sentiment_df[sentiment_df["userid"] == user_id]
    churn_row = df_churn[df_churn["userid"] == user_id]

    if row_a.empty or churn_row.empty:
        print(f"❌ User {user_id} not found in base dataset.")
        return

    # === Get Churn Probability and Risk ===
    churn_prob = churn_row.iloc[0]["churn_probability (%)"]
    risk = churn_row.iloc[0]["churn_risk"]

    # === SHAP - Model A ===
    X_a = row_a[features_a]
    shap_vals_a = explainer_a.shap_values(X_a)
    shap_df = pd.DataFrame({
        "feature": features_a,
        "value": X_a.values[0],
        "shap_value": shap_vals_a[0],
        "model": "Model A"
    })

    # === SHAP - Model B (compound_score) if available ===
    model_b_used = False
    if not row_b.empty and "compound_score" in row_b.columns:
        X_b = row_b[["compound_score"]]
        shap_vals_b = explainer_b.shap_values(X_b)
        shap_b_df = pd.DataFrame({
            "feature": ["compound_score"],
            "value": X_b.values[0],
            "shap_value": shap_vals_b[0],
            "model": ["Model B"]
        })
        shap_df = pd.concat([shap_df, shap_b_df])
        model_b_used = True

    # === Top Features ===
    shap_df["abs_val"] = shap_df["shap_value"].abs()
    top_df = shap_df.sort_values("abs_val", ascending=False).head(5)

    # === Chart ===
    plt.figure(figsize=(8, 5))
    colors = ['#FF9999' if m == 'Model A' else '#9999FF' for m in top_df["model"]]
    plt.barh(top_df["feature"], top_df["shap_value"], color=colors)
    plt.xlabel("SHAP Value")
    plt.title(f"User {user_id} Churn: {churn_prob:.2f}% ({risk} Risk)")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    chart_path = os.path.join(CHART_DIR, f"user_{user_id}.png")
    plt.savefig(chart_path)
    plt.close()

    # === Recommendations ===
    combined_row = row_a.iloc[0].to_dict()
    if not sentiment.empty:
        combined_row["compound_score"] = sentiment.iloc[0]["compound_score"]
    recs = build_recommendations(combined_row)

    # === Final Output ===
    output_data = {
        "user_id": int(user_id),
        "churn_probability": round(float(churn_prob), 2),
        "risk_level": str(risk),
        "top_features": top_df[["feature", "value", "shap_value", "model"]].to_dict(orient="records"),
        "recommendations": recs,
        "chart_path": chart_path,
        "model_b_used": model_b_used
    }

    # === Save JSON ===
    with open(os.path.join(EXPLAIN_DIR, f"user_{user_id}.json"), "w") as f:
        json.dump(output_data, f, indent=2)

    # === Print Summary to Console ===
    print(f"[OK] Generated explanation for user {user_id}")


def main():
    parser = argparse.ArgumentParser(description="Generate user explanations and charts")
    parser.add_argument("user_id", nargs="?", type=int, help="User ID to generate (omit with --all)")
    parser.add_argument("--all", action="store_true", help="Generate for all users in churn_prediction.csv")
    args = parser.parse_args()

    if args.all:
        for uid in df_churn["userid"].astype(int).tolist():
            try:
                generate_for_user(uid)
            except Exception as e:
                print(f"[WARN] Skipped user {uid}: {e}")
        return

    if args.user_id is None:
        print("❌ Provide a user_id or use --all")
        sys.exit(1)

    generate_for_user(int(args.user_id))

if __name__ == "__main__":
    main()

