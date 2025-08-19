"""
This script orchestrates post-upload processing:
- Detects new preprocessed uploads at `datasets/user-uploads-preprocessed.csv`
- Splits main dataset for Model A and Model B training
- Triggers model training based on counters
- Archives a COPY of the preprocessed uploads while keeping the original file intact
"""
import os
import json
import time
import pandas as pd
from pathlib import Path
import subprocess
import sys
from datetime import datetime
import shutil

# === Configuration ===
FREQ_MODEL_A = 20  # Train Model A every 20 new records
FREQ_MODEL_B = 10  # Train Model B every 10 new records

# === Paths ===
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / 'datasets'
MODEL_A_TRAIN = DATASET_DIR / 'model_a_train.csv'
MODEL_B_TRAIN = DATASET_DIR / 'model_b_train.csv'
MAIN_DATASET = DATASET_DIR / 'main-dataset.csv'
PREPROCESSED_UPLOADS = DATASET_DIR / 'user-uploads-preprocessed.csv'

# Model scripts
TRAIN_MODEL_A = BASE_DIR / 'scripts' / 'train_model_a.py'
TRAIN_MODEL_B = BASE_DIR / 'scripts' / 'train_model_b.py'
# Post-train/update scripts
CHURN_PRED_SCRIPT = BASE_DIR / 'scripts' / 'churn_prediction.py'
EXPLAIN_ALL_SCRIPT = BASE_DIR / 'scripts' / 'explain_user.py'
EXPLAINABLE_AI_SCRIPT = BASE_DIR / 'scripts' / 'explinableAI.py'

# Counters for tracking new records
COUNTER_FILE = DATASET_DIR / 'training_counters.json'

def load_counters():
    """Load the training counters from file."""
    if COUNTER_FILE.exists():
        with open(COUNTER_FILE, 'r') as f:
            return json.load(f)
    return {'model_a': 0, 'model_b': 0}

def save_counters(counters):
    """Save the training counters to file."""
    with open(COUNTER_FILE, 'w') as f:
        json.dump(counters, f)

def split_dataset():
    """Split the latest preprocessed uploads into model A and model B datasets.

    Returns a dict with counts: {"total": int, "with_reviews": int}
    """
    if not PREPROCESSED_UPLOADS.exists() or os.path.getsize(PREPROCESSED_UPLOADS) == 0:
        print("❌ Preprocessed uploads not found or empty!")
        return False
    
    print("🔍 Loading preprocessed uploads dataset...")
    df = pd.read_csv(PREPROCESSED_UPLOADS)
    
    # Cap usage values for all Day_ columns (both models)
    day_columns = [col for col in df.columns if col.startswith("Day_")]
    if day_columns:
        df[day_columns] = df[day_columns].clip(upper=300)
    
    # Split for Model B: Only users who left a review
    print("💾 Creating dataset for Model B (users with reviews)...")
    model_b_df = df[df['review'].notna() & df['review'].str.strip().ne("")].copy()
    
    # Split for Model A: Drop unstructured column (review only)
    print("💾 Creating dataset for Model A (all users)...")
    model_a_df = df.drop(columns=['review'], errors='ignore').copy()
    
    # Save both datasets with append/merge semantics (dedupe by userid)
    def append_or_create_csv(new_df: pd.DataFrame, target_path: Path) -> None:
        try:
            if target_path.exists() and os.path.getsize(target_path) > 0:
                existing_df = pd.read_csv(target_path)
                # Align columns (union) and fill missing
                for col in new_df.columns:
                    if col not in existing_df.columns:
                        existing_df[col] = 0 if new_df[col].dtype != 'O' else ''
                for col in existing_df.columns:
                    if col not in new_df.columns:
                        new_df[col] = 0 if existing_df[col].dtype != 'O' else ''
                combined_df = pd.concat([existing_df[new_df.columns], new_df[new_df.columns]], ignore_index=True)
                if 'userid' in combined_df.columns:
                    combined_df.drop_duplicates(subset=['userid'], keep='last', inplace=True)
                combined_df.to_csv(target_path, index=False)
            else:
                new_df.to_csv(target_path, index=False)
        except Exception as e:
            fallback_path = target_path.parent / f"{target_path.stem}_append_error_{int(time.time())}.csv"
            new_df.to_csv(fallback_path, index=False)
            print(f"⚠️ Append error for {target_path.name}: {e}. Wrote batch to {fallback_path}")

    append_or_create_csv(model_a_df, MODEL_A_TRAIN)
    append_or_create_csv(model_b_df, MODEL_B_TRAIN)
    
    total_len = len(df)
    with_reviews_len = len(model_b_df)
    print(f"✅ Split complete (uploads batch): {total_len} total users, {with_reviews_len} with reviews")
    return {"total": total_len, "with_reviews": with_reviews_len}

def train_model(script_path, model_name):
    """Train a model using the specified script."""
    print(f"\n🚀 Training {model_name}...")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {model_name} training completed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error training {model_name}:")
        print(e.stderr)
        return False

def run_script(script_path: Path, args: list[str] | None = None, name: str = "script") -> bool:
    """Run a Python script with optional args; return True if successful."""
    if args is None:
        args = []
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), *args],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"[OK] {name} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] {name} failed: {e.stderr}")
        return False

def process_new_data():
    """Process new data and trigger model training as needed."""
    # Check if there's new preprocessed data
    if not PREPROCESSED_UPLOADS.exists() or os.path.getsize(PREPROCESSED_UPLOADS) == 0:
        print("ℹ️ No new preprocessed data found.")
        return
    
    print(f"📊 Found new preprocessed data at {PREPROCESSED_UPLOADS}")
    # Determine number of new records in this batch
    try:
        uploads_batch_df = pd.read_csv(PREPROCESSED_UPLOADS)
        new_records_count = len(uploads_batch_df)
    except Exception:
        new_records_count = 1
    
    # Split the dataset
    split_counts = split_dataset()
    if not split_counts:
        return
    
    # Load and update counters
    counters = load_counters()
    counters['model_a'] += int(split_counts.get('total', new_records_count))
    counters['model_b'] += int(split_counts.get('with_reviews', 0))
    print(f"📈 Counters updated: +A={split_counts.get('total', 0)}, +B={split_counts.get('with_reviews', 0)} → A={counters['model_a']}, B={counters['model_b']}")
    
    # Check if it's time to train Model A
    if counters['model_a'] >= FREQ_MODEL_A:
        print(f"\n⏰ Time to train Model A (every {FREQ_MODEL_A} new records)")
        # Only train if dataset exists and has rows
        can_train_a = MODEL_A_TRAIN.exists() and os.path.getsize(MODEL_A_TRAIN) > 0
        if can_train_a and train_model(TRAIN_MODEL_A, "Model A"):
            counters['model_a'] = 0
        elif not can_train_a:
            print("⚠️ Skipping Model A training: model_a_train.csv is missing or empty")
    
    # Check if it's time to train Model B
    if counters['model_b'] >= FREQ_MODEL_B:
        print(f"\n⏰ Time to train Model B (every {FREQ_MODEL_B} new records)")
        # Only train if dataset exists and has rows (>0 with reviews)
        can_train_b = MODEL_B_TRAIN.exists() and os.path.getsize(MODEL_B_TRAIN) > 0
        if can_train_b:
            trained_ok = train_model(TRAIN_MODEL_B, "Model B")
            if trained_ok:
                counters['model_b'] = 0
        elif not can_train_b:
            print("⚠️ Skipping Model B training: no rows with reviews in model_b_train.csv")
    
    # Save updated counters
    save_counters(counters)
    
    # Always refresh downstream artifacts so frontend reflects new data promptly
    run_script(CHURN_PRED_SCRIPT, name="churn_prediction")
    # Generate/refresh explanations and charts for all users
    # Uses --all to ensure new users are covered immediately
    run_script(EXPLAIN_ALL_SCRIPT, args=["--all"], name="explain_user --all")
    # Also run business-friendly explainer that enriches top features and descriptions
    run_script(EXPLAINABLE_AI_SCRIPT, name="explinableAI (full refresh)")

    # Archive a copy of the preprocessed file but keep the original available
    archive_path = DATASET_DIR / 'archived_uploads' / f"preprocessed_{int(time.time())}.csv"
    os.makedirs(archive_path.parent, exist_ok=True)
    shutil.copy(str(PREPROCESSED_UPLOADS), str(archive_path))
    print(f"📦 Archived a copy of preprocessed data to {archive_path}")

if __name__ == "__main__":
    print(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting data processing")
    process_new_data()
    print("✅ Processing complete!")

# Add this to the end of process_upload.py to automatically trigger processing
# from scripts.process_new_data import process_new_data
# process_new_data()
