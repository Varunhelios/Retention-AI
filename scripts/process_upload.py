# This script processes newly uploaded user rows from `datasets/user-uploads.csv`.
# It ensures each row has a unique `userid`, appends the rows to `datasets/main-dataset.csv`,
# saves a preprocessed copy, triggers the downstream pipeline, and then clears the uploads file.
import pandas as pd
import os
import sys
from pathlib import Path
import shutil
import json

def preprocess_dataframe(df):
    """Apply the same preprocessing as in preprocess_main_dataset.py"""
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Exclude these columns from numeric preprocessing
    exclude_cols = ['userid', 'review', 'left_review', 'is_churned']
    numeric_cols = df_clean.select_dtypes(include=['float64', 'int64']).columns.difference(exclude_cols).tolist()
    
    # Fill missing numeric values with column mean
    if numeric_cols:
        df_clean[numeric_cols] = df_clean[numeric_cols].fillna(df_clean[numeric_cols].mean())
    
    return df_clean

def process_user_uploads():
    # Define file paths
    base_dir = Path(__file__).parent.parent
    uploads_path = base_dir / 'datasets' / 'user-uploads.csv'
    preprocessed_uploads_path = base_dir / 'datasets' / 'user-uploads-preprocessed.csv'
    main_dataset_path = base_dir / 'datasets' / 'main-dataset.csv'
    cleaned_dataset_path = base_dir / 'datasets' / 'cleaned-dataset.csv'
    
    # Check if uploads file exists and has data
    if not uploads_path.exists() or os.path.getsize(uploads_path) == 0:
        print("No new uploads to process.")
        return
    
    try:
        # Read the uploads file
        uploads_df = pd.read_csv(uploads_path)
        
        # Check if there's any data to process
        if uploads_df.empty:
            print("No new data to process in uploads file.")
            return 0
            
        # 1. Always assign fresh sequential userids, then append to main-dataset.csv
        #    Policy: ignore any incoming 'userid' values in uploads to keep IDs managed centrally.
        if main_dataset_path.exists() and os.path.getsize(main_dataset_path) > 0:
            main_df = pd.read_csv(main_dataset_path)
            if 'Unnamed: 0' in main_df.columns:
                main_df.drop(columns=['Unnamed: 0'], inplace=True)

            # Determine the starting userid from existing main dataset
            last_userid = int(main_df['userid'].max()) if 'userid' in main_df.columns else 1999

            # Drop any provided userids and assign fresh contiguous IDs
            if 'userid' in uploads_df.columns:
                uploads_df = uploads_df.drop(columns=['userid'])
            new_userid_start = last_userid + 1
            uploads_df.insert(0, 'userid', range(new_userid_start, new_userid_start + len(uploads_df)))

            # Reorder columns to match main dataset when possible
            if 'userid' in main_df.columns:
                # Add any missing columns to uploads_df
                for col in main_df.columns:
                    if col not in uploads_df.columns:
                        uploads_df[col] = ''
                uploads_df = uploads_df[main_df.columns]

            combined_raw = pd.concat([main_df, uploads_df], ignore_index=True)
        else:
            # No main dataset yet: assign from 2000 upwards irrespective of incoming values
            if 'userid' in uploads_df.columns:
                uploads_df = uploads_df.drop(columns=['userid'])
            new_userid_start = 2000
            uploads_df.insert(0, 'userid', range(new_userid_start, new_userid_start + len(uploads_df)))
            combined_raw = uploads_df
        
        # Save the assigned user IDs back to user-uploads.csv first
        # Ensure userid is the first column when saving back to user-uploads.csv
        if 'userid' in uploads_df.columns and uploads_df.columns[0] != 'userid':
            cols = ['userid'] + [col for col in uploads_df.columns if col != 'userid']
            uploads_df = uploads_df[cols]
        
        # Save the combined data to main-dataset.csv
        try:
            # Make sure the directory exists
            main_dataset_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with explicit encoding and line terminator for Windows
            combined_raw.to_csv(main_dataset_path, index=False, encoding='utf-8', lineterminator='\n')
            print(f"✅ Successfully saved {len(combined_raw)} total records to main-dataset.csv")
            
            # Also save the uploads with the assigned user IDs
            uploads_df.to_csv(uploads_path, index=False, encoding='utf-8', lineterminator='\n')
            print(f"✅ Updated user-uploads.csv with {len(uploads_df)} records")
            
        except Exception as e:
            print(f"❌ Error saving to CSV files: {str(e)}")
            raise
        
        # 2. Preprocess the newly added data
        print("Preprocessing data...")
        preprocessed_df = preprocess_dataframe(uploads_df)
        
        # Save preprocessed data to user-uploads-preprocessed.csv
        preprocessed_df.to_csv(preprocessed_uploads_path, index=False)
        print(f"✅ Preprocessed data saved to {preprocessed_uploads_path}")
        
        # 3. Trigger the data processing pipeline (splitting and model training)
        print("\n🔄 Triggering data processing pipeline...")
        try:
            # Add the scripts directory to the path
            import sys
            scripts_dir = str(Path(__file__).parent.absolute())
            if scripts_dir not in sys.path:
                sys.path.append(scripts_dir)
            from process_new_data import process_new_data
            process_new_data()
        except Exception as e:
            import traceback
            print(f"⚠️ Error in data processing pipeline: {str(e)}")
            print(traceback.format_exc())
        
        # Clear the original uploads file after successful processing
        with open(uploads_path, 'w') as f:
            f.write('')
        print("✅ Cleared the uploads file after successful processing")
        
        # Log the assigned userid range
        try:
            print(f"Successfully processed {len(uploads_df)} new user(s) with userids from {new_userid_start} to {new_userid_start + len(uploads_df) - 1}")
        except Exception:
            # Fallback if variable not set due to unexpected path
            print(f"Successfully processed {len(uploads_df)} new user(s).")
        
        # Return the number of new records for potential further processing
        return len(preprocessed_df)
        
    except Exception as e:
        print(f"Error processing uploads: {str(e)}")
        return 0

def main():
    # Process new uploads (this already triggers downstream processing internally)
    # Avoid double-triggering here to prevent duplicate training attempts.
    process_user_uploads()

if __name__ == "__main__":
    main()
