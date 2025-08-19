import os
import pandas as pd

# === Paths ===
main_dataset_path = "datasets/main-dataset.csv"
cleaned_dataset_path = "datasets/cleaned-dataset.csv"

# === Ensure folders exist ===
os.makedirs("datasets", exist_ok=True)

# === Load main dataset ===
df = pd.read_csv(main_dataset_path)

# === Drop index column if it exists ===
if "Unnamed: 0" in df.columns:
    df.drop(columns=["Unnamed: 0"], inplace=True)

# === Exclude these columns from numeric preprocessing
exclude_cols = ['userid', 'review', 'left_review', 'is_churned']
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.difference(exclude_cols).tolist()

# === Fill missing numeric values with column mean
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

# === Save cleaned dataset
df.to_csv(cleaned_dataset_path, index=False)
print(f"✅ Cleaned dataset saved to {cleaned_dataset_path}")
