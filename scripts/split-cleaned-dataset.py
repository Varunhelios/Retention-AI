"""
Splits the full cleaned dataset into training datasets for Model A and Model B.
Change: preserve existing train datasets by append/merge (no overwrite).
Merges on `userid`, keeping the latest row for duplicates.
"""
import os
import pandas as pd

# === Paths ===
DATASET_DIR = "datasets"
os.makedirs(DATASET_DIR, exist_ok=True)

CLEANED_PATH = os.path.join(DATASET_DIR, "cleaned-dataset.csv")
MODEL_A_PATH = os.path.join(DATASET_DIR, "model_a_train.csv")
MODEL_B_PATH = os.path.join(DATASET_DIR, "model_b_train.csv")

# === Load cleaned dataset
df = pd.read_csv(CLEANED_PATH)
print(f"✅ Loaded cleaned dataset with shape: {df.shape}")

# === Cap usage values for all Day_ columns (both models)
day_columns = [col for col in df.columns if col.startswith("Day_")]
df[day_columns] = df[day_columns].clip(upper=300)

# === Split for Model B: Only users who left a review
model_b_df = df[df['review'].notna() & df['review'].str.strip().ne("")].copy()

# === Split for Model A: Drop unstructured column (review only)
model_a_df = df.drop(columns=['review'], errors='ignore').copy()

# === Save splits with append/merge (preserve history)
def save_append_merge(new_df: pd.DataFrame, path: str, key: str = 'userid'):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            existing = pd.read_csv(path)
            # Align union of columns
            for col in new_df.columns:
                if col not in existing.columns:
                    existing[col] = 0 if new_df[col].dtype != 'O' else ''
            for col in existing.columns:
                if col not in new_df.columns:
                    new_df[col] = 0 if existing[col].dtype != 'O' else ''
            # Same column order as new_df for stability
            combined = pd.concat([existing[new_df.columns], new_df[new_df.columns]], ignore_index=True)
            if key in combined.columns:
                combined.drop_duplicates(subset=[key], keep='last', inplace=True)
            combined.to_csv(path, index=False)
        except Exception:
            new_df.to_csv(path, index=False)
    else:
        new_df.to_csv(path, index=False)

save_append_merge(model_a_df, MODEL_A_PATH)
save_append_merge(model_b_df, MODEL_B_PATH)

print(f"📁 model_a_train.csv saved: {model_a_df.shape}")
print(f"📁 model_b_train.csv saved: {model_b_df.shape}")
