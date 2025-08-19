import os
import json
import joblib
import shap
import pandas as pd

# THIS LINE is what fixes the GUI crash (must come BEFORE pyplot)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# === File Paths ===
DATASET_DIR = "datasets"
MODEL_DIR = "models"
OUTPUT_DIR = "outputs"
EXPLAIN_DIR = os.path.join(OUTPUT_DIR, "explanations")
CHART_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(EXPLAIN_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# === Load Files ===
df_churn = pd.read_csv(os.path.join(DATASET_DIR, "churn_prediction.csv"))
df_a = pd.read_csv(os.path.join(DATASET_DIR, "model_a_train.csv"))
df_b = pd.read_csv(os.path.join(DATASET_DIR, "model_b_train.csv"))
sentiment_df = pd.read_csv(os.path.join(DATASET_DIR, "sentiment_analysis.csv"))

model_a = joblib.load(os.path.join(MODEL_DIR, "model_a_latest.pkl"))
model_b = joblib.load(os.path.join(MODEL_DIR, "model_b_latest.pkl"))
with open(os.path.join(MODEL_DIR, "model_a_features.json")) as f:
    features_a = json.load(f)

explainer_a = shap.TreeExplainer(model_a)
explainer_b = shap.TreeExplainer(model_b)

# === Feature Descriptions and Plain English Explanations ===
FEATURE_DESCRIPTIONS = {
    'total_days_active': 'User Tenure',
    'Average_Screen_Time': 'Daily App Usage',
    'Last_Visited_Minutes': 'Time Since Last Visit',
    'Day_1': 'Week 1 Engagement',
    'Day_2': 'Week 1 Engagement', 
    'Day_3': 'Week 1 Engagement',
    'Day_4': 'Week 1 Engagement',
    'Day_5': 'Week 1 Engagement',
    'Day_6': 'Week 1 Engagement',
    'Day_7': 'Week 1 Engagement',
    'Day_8': 'Week 2 Engagement',
    'Day_9': 'Week 2 Engagement',
    'Day_10': 'Week 2 Engagement',
    'Day_11': 'Week 2 Engagement',
    'Day_12': 'Week 2 Engagement',
    'Day_13': 'Week 2 Engagement',
    'Day_14': 'Week 2 Engagement',
    'Day_15': 'Week 3 Engagement',
    'Day_16': 'Week 3 Engagement',
    'Day_17': 'Week 3 Engagement',
    'Day_18': 'Week 3 Engagement',
    'Day_19': 'Week 3 Engagement',
    'Day_20': 'Week 3 Engagement',
    'Day_21': 'Week 3 Engagement',
    'Day_22': 'Week 4 Engagement',
    'Day_23': 'Week 4 Engagement',
    'Day_24': 'Week 4 Engagement',
    'Day_25': 'Week 4 Engagement',
    'Day_26': 'Week 4 Engagement',
    'Day_27': 'Week 4 Engagement',
    'Day_28': 'Week 4 Engagement',
    'Day_29': 'Week 5 Engagement',
    'Day_30': 'Week 5 Engagement',
    'compound_score': 'User Satisfaction Score',
    'Ratings': 'App Rating Given',
    'New_Password_Request': 'Account Security Issues'
}

# Business-friendly feature groupings
BUSINESS_CATEGORIES = {
    'User Tenure': 'How long the user has been with us',
    'Daily App Usage': 'How much time they spend in the app daily',
    'Time Since Last Visit': 'How recently they used the app',
    'Week 1 Engagement': 'Activity level during their first week',
    'Week 2 Engagement': 'Activity level during their second week', 
    'Week 3 Engagement': 'Activity level during their third week',
    'Week 4 Engagement': 'Activity level during their fourth week',
    'Week 5 Engagement': 'Activity level during their fifth week',
    'User Satisfaction Score': 'Overall satisfaction based on feedback',
    'App Rating Given': 'Rating they gave our app',
    'Account Security Issues': 'Password reset requests indicating friction'
}

def get_plain_english_explanation(feature_name, value, shap_value):
    """Convert SHAP values to plain English explanations"""
    impact_direction = "increases" if shap_value > 0 else "reduces"
    
    # Determine impact strength based on SHAP value magnitude
    if abs(shap_value) > 0.3:
        impact_strength = "significantly"
    elif abs(shap_value) > 0.1:
        impact_strength = "moderately"
    else:
        impact_strength = "slightly"
    
    # Business-friendly explanations
    if 'Tenure' in feature_name or feature_name == 'total_days_active':
        if value < 7:
            return f"🆕 New user (only {int(value)} days) - {impact_strength} {impact_direction} churn risk. New users need extra attention."
        elif value < 30:
            return f"📈 Growing user ({int(value)} days) - {impact_strength} {impact_direction} churn risk. Still in critical onboarding period."
        else:
            return f"🏆 Established user ({int(value)} days) - {impact_strength} {impact_direction} churn risk. Long-term relationship built."
    
    elif 'Daily App Usage' in feature_name or feature_name == 'Average_Screen_Time':
        if value < 30:
            return f"⚠️ Low engagement ({int(value)} min/day) - {impact_strength} {impact_direction} churn risk. User barely uses the app."
        elif value < 120:
            return f"📱 Moderate usage ({int(value)} min/day) - {impact_strength} {impact_direction} churn risk. Decent but could improve."
        else:
            return f"🔥 Power user ({int(value)} min/day) - {impact_strength} {impact_direction} churn risk. Highly engaged!"
    
    elif 'Time Since Last Visit' in feature_name:
        hours = value / 60
        if hours < 24:
            return f"✅ Recent user (last seen {hours:.1f} hours ago) - {impact_strength} {impact_direction} churn risk. Active recently."
        elif hours < 168:  # 1 week
            return f"⏰ Inactive for {hours/24:.1f} days - {impact_strength} {impact_direction} churn risk. Starting to drift away."
        else:
            return f"🚨 Long absence ({hours/24:.0f} days ago) - {impact_strength} {impact_direction} churn risk. May have already churned."
    
    elif 'Week' in feature_name and 'Engagement' in feature_name:
        week_num = feature_name.split()[1]
        if value == 0:
            return f"😴 No activity in {feature_name.lower()} - {impact_strength} {impact_direction} churn risk. User was disengaged this week."
        elif value < 3:
            return f"📉 Low activity in {feature_name.lower()} ({int(value)} sessions) - {impact_strength} {impact_direction} churn risk."
        else:
            return f"🎯 Good activity in {feature_name.lower()} ({int(value)} sessions) - {impact_strength} {impact_direction} churn risk."
    
    elif 'Satisfaction' in feature_name or feature_name == 'compound_score':
        if value < -0.3:
            return f"😞 Very negative feedback (score: {value:.2f}) - {impact_strength} {impact_direction} churn risk. User is unhappy."
        elif value < -0.1:
            return f"😐 Somewhat negative feedback (score: {value:.2f}) - {impact_strength} {impact_direction} churn risk. Some concerns."
        elif value > 0.3:
            return f"😊 Very positive feedback (score: {value:.2f}) - {impact_strength} {impact_direction} churn risk. User loves the app!"
        elif value > 0.1:
            return f"🙂 Positive feedback (score: {value:.2f}) - {impact_strength} {impact_direction} churn risk. Generally satisfied."
        else:
            return f"😶 Neutral feedback (score: {value:.2f}) - {impact_strength} {impact_direction} churn risk. No strong opinion."
    
    elif 'Rating' in feature_name:
        if value >= 4:
            return f"⭐ High rating ({value}/5 stars) - {impact_strength} {impact_direction} churn risk. User appreciates the app."
        elif value >= 3:
            return f"⭐ Average rating ({value}/5 stars) - {impact_strength} {impact_direction} churn risk. Room for improvement."
        else:
            return f"⭐ Low rating ({value}/5 stars) - {impact_strength} {impact_direction} churn risk. User is dissatisfied."
    
    elif 'Security Issues' in feature_name or 'Password' in feature_name:
        if value == 0:
            return f"🔒 No password issues - {impact_strength} {impact_direction} churn risk. Smooth user experience."
        elif value == 1:
            return f"🔑 One password reset - {impact_strength} {impact_direction} churn risk. Minor friction experienced."
        else:
            return f"🚨 Multiple password resets ({int(value)}) - {impact_strength} {impact_direction} churn risk. Significant login friction."
    
    # Fallback for any unmapped features
    return f"📊 {feature_name}: {value} - {impact_strength} {impact_direction} churn risk"

# === Feature-based Recommendation Logic ===
def get_recommendations(row):
    recs = []
    
    # Define recommendation categories with weights and messages
    recommendations = []
    
    # 1. Critical Issues (Highest Priority)
    if row.get("New Password Request", 0) > 5:
        recommendations.append((100, "Having trouble with your account? Our support team is here to help!"))
    
    # 2. Negative Sentiment (High Priority)
    sentiment = row.get("compound_score")
    if pd.notna(sentiment) and sentiment < -0.2:
        recommendations.append((90, "We'd love to hear how we can improve your experience. Share your feedback with us!"))
    
    # 3. Low Ratings (High Priority)
    rating = row.get("Ratings", 0)
    if 0 < rating <= 5:
        recommendations.append((85, "We're working hard to improve. Your feedback is valuable to us!"))
    
    # 4. Inactive Users (Medium-High Priority)
    last_visit_mins = row.get("Last Visited Minutes", 0)
    if last_visit_mins > 10080:  # More than 1 week
        recommendations.append((80, "We've missed you! Check out what's new since your last visit."))
    
    # 5. New Users (Medium Priority)
    days_active = row.get("total_days_active", 0)
    if days_active < 7:
        recommendations.append((70, "Complete our onboarding tutorial to make the most of your experience."))
    
    # 6. Activity Drop (Medium Priority)
    screen_time = row.get("Average Screen Time", 0)
    recent_days = [f"Day_{i}" for i in range(1, 8)]  # Last 7 days
    recent_activity = sum(row.get(day, 0) for day in recent_days if isinstance(row.get(day), (int, float)))
    if recent_activity < (screen_time * 0.5) and screen_time > 0:
        recommendations.append((65, "We've noticed you've been less active recently. Check out what's new!"))
    
    # 7. High-Value Users (Medium Priority)
    avg_spend = row.get("Average Spent on App (INR)", 0)
    if avg_spend > 500:
        recommendations.append((60, "As a valued customer, check out our premium features for an enhanced experience."))
    
    # 8. Screen Time (Low-Medium Priority)
    if screen_time > 240:
        recommendations.append((50, "Consider our screen time management features to help maintain a healthy digital balance."))
    elif screen_time < 30 and days_active > 7:  # Not new but low engagement
        recommendations.append((45, "Explore our app's key features to enhance your daily productivity and experience."))
    
    # 9. Upsell Opportunities (Low Priority)
    if avg_spend < 100 and screen_time > 60:
        recommendations.append((40, "Discover our premium features that could enhance your daily experience."))
    
    # 10. Positive Feedback (Low Priority)
    if pd.notna(sentiment) and sentiment > 0.2:
        recommendations.append((30, "Love having you! Consider sharing your experience in a review."))
    
    # First, collect all unique recommendations
    unique_recs = []
    seen = set()
    
    # Add all recommendations from our priority list
    for score, rec in sorted(recommendations, reverse=True, key=lambda x: x[0]):
        if rec not in seen:
            seen.add(rec)
            unique_recs.append(rec)
    
    # Always available fallback recommendations
    fallbacks = [
        "Discover new features in our latest update!",
        "Check out our tips & tricks section to get the most out of our app.",
        "Join our community to connect with other users and share experiences.",
        "Explore our premium features for an enhanced experience.",
        "Take a quick tour to discover what's new in the app.",
        "Complete your profile to get personalized recommendations.",
        "Learn how to use our most popular features with our quick start guide.",
        "Enable notifications to stay updated with important information.",
        "Customize your dashboard for a better user experience.",
        "Check out our help center for answers to common questions."
    ]
    
    # Add fallbacks until we have 3 recommendations
    for fallback in fallbacks:
        if len(unique_recs) >= 3:
            break
        if fallback not in seen:
            unique_recs.append(fallback)
    
    # If we still don't have 3, add generic ones
    generic_count = 1
    while len(unique_recs) < 3:
        unique_recs.append(f"Helpful tip #{generic_count}: Explore our app to discover more!")
        generic_count += 1
    
    # Ensure we return exactly 3
    return unique_recs[:3]

# === Main Loop for Users ===
for _, user_row in df_churn.iterrows():
    user_id = user_row["userid"]
    churn_prob = user_row["churn_probability (%)"]
    risk = user_row["churn_risk"]

    row_a = df_a[df_a["userid"] == user_id]
    row_b = df_b[df_b["userid"] == user_id]
    sentiment = sentiment_df[sentiment_df["userid"] == user_id]

    if row_a.empty:
        continue

    model_b_used = False

    # SHAP for Model A
    X_a = row_a[features_a]
    shap_vals_a = explainer_a.shap_values(X_a)
    
    # Create a mapping of feature names to their display names
    feature_display_names = {}
    for feature in features_a:
        if feature in FEATURE_DESCRIPTIONS:
            feature_display_names[feature] = FEATURE_DESCRIPTIONS[feature]
        else:
            # Handle any unmapped features with a fallback
            feature_display_names[feature] = feature.replace('_', ' ').title()
    
    # Get display names in the same order as features
    display_names = [feature_display_names.get(f, f) for f in features_a]
    
    # Get the index of the current user in the filtered dataframe
    user_idx = df_a[df_a["userid"] == user_id].index[0]
    X_a = df_a[df_a["userid"] == user_id][features_a]
    
    # Create SHAP values dataframe with the correct user's data
    shap_values = shap_vals_a[0] if len(X_a) == 1 else shap_vals_a[0][0]
    
    # Generate descriptions and explanations for each feature
    descriptions = []
    explanations = []
    for i, (feature_name, display_name) in enumerate(zip(features_a, display_names)):
        value = X_a.loc[user_idx].values[i]
        shap_val = shap_values[i]
        
        # Get description from our business categories
        desc = BUSINESS_CATEGORIES.get(display_name, display_name)
        descriptions.append(desc)
        
        # Get plain English explanation using the display name
        explanation = get_plain_english_explanation(display_name, value, shap_val)
        explanations.append(explanation)
    
    shap_df = pd.DataFrame({
        "feature": display_names,  # Use business-friendly display names
        "value": X_a.loc[user_idx].values,
        "shap_value": shap_values,
        "model": "Model A",
        "description": descriptions,  # Add business category descriptions
        "explanation": explanations,  # Add plain English explanations
        "impact": abs(shap_values)  # Calculate impact as absolute value of SHAP
    })

    # SHAP for Model B if review exists
    if not row_b.empty and "compound_score" in row_b.columns:
        X_b = row_b[["compound_score"]]
        shap_vals_b = explainer_b.shap_values(X_b)
        
        # Generate explanation for sentiment score
        sentiment_value = X_b.values[0][0]
        sentiment_shap = shap_vals_b[0][0]
        sentiment_explanation = get_plain_english_explanation("Sentiment Score", sentiment_value, sentiment_shap)
        
        shap_b_df = pd.DataFrame({
            "feature": ["Sentiment Score"],  # More descriptive name
            "value": X_b.values[0],
            "shap_value": shap_vals_b[0],
            "model": ["Model B"],
            "description": ["User sentiment from reviews/feedback"],
            "explanation": [sentiment_explanation],
            "impact": [abs(sentiment_shap)]
        })
        shap_df = pd.concat([shap_df, shap_b_df])
        model_b_used = True

    # Get top 5 features
    shap_df["abs_val"] = shap_df["shap_value"].abs()
    top_df = shap_df.sort_values("abs_val", ascending=False).head(5)

    # SHAP Bar Chart (Non-GUI Safe)
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

    # Build recommendation row from Model A features (not just churn CSV)
    combined_row = row_a.iloc[0].to_dict()
    # Merge sentiment if available
    if not sentiment.empty:
        combined_row.update(sentiment.iloc[0].to_dict())
    
    # Debug: Print the combined row to verify data
    print(f"\nProcessing user {user_id}:")
    print(f"- Screen Time: {combined_row.get('Average Screen Time', 'N/A')}")
    print(f"- Last Visit: {combined_row.get('Last Visited Minutes', 'N/A')} mins")
    print(f"- Days Active: {combined_row.get('total_days_active', 'N/A')}")
    print(f"- Sentiment: {combined_row.get('compound_score', 'N/A')}")
    print(f"- Raw user data sample: {dict(list(combined_row.items())[:3])}...")

    # Get recommendations
    recommendations = get_recommendations(combined_row)
    print(f"Generated {len(recommendations)} recommendations:", recommendations)

    # Final output JSON with exact format
    output_data = {
        "user_id": int(user_id),
        "churn_probability": round(churn_prob, 2),
        "risk_level": risk,
        "top_features": top_df[["feature", "value", "shap_value", "model", "description", "explanation"]].to_dict(orient="records"),
        "recommendations": recommendations,  # Now includes all 3 recommendations
        "chart_path": f"outputs/charts/user_{user_id}.png",  # Use forward slashes for web compatibility
        "model_b_used": model_b_used
    }

    with open(os.path.join(EXPLAIN_DIR, f"user_{user_id}.json"), "w") as f:
        json.dump(output_data, f, indent=2)

print(" All user explanations generated in outputs/explanations/")
