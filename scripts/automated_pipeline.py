import os
import time
import logging
import schedule
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / 'datasets'
UPLOAD_FILE = DATASET_DIR / 'user-uploads.csv'
PREPROCESSED_FILE = DATASET_DIR / 'user-uploads-preprocessed.csv'
COUNTER_FILE = DATASET_DIR / 'training_counters.json'

# Check interval (in seconds)
CHECK_INTERVAL = 300  # Check for new data every 5 minutes

# Thresholds for retraining based on new data
FREQ_MODEL_A = 20  # Retrain Model A after 20 new records
FREQ_MODEL_B = 10  # Retrain Model B after 10 new records

def load_counters():
    """Load the training counters from file."""
    if COUNTER_FILE.exists():
        try:
            with open(COUNTER_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Corrupted counters file, resetting counters")
    return {'model_a': 0, 'model_b': 0, 'last_retrain_a': None, 'last_retrain_b': None}

def save_counters(counters):
    """Save the training counters to file."""
    with open(COUNTER_FILE, 'w') as f:
        json.dump(counters, f, indent=2)

def run_script(script_name):
    """Run a Python script and return True if successful."""
    script_path = BASE_DIR / 'scripts' / f"{script_name}.py"
    try:
        logger.info(f"Running {script_name}...")
        result = subprocess.run(
            ['python', str(script_path)],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"{script_name} completed successfully")
        if result.stdout:
            logger.debug(f"{script_name} output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e.stderr}")
        return False

def check_for_new_data():
    """Check for new user uploads and process them."""
    if not UPLOAD_FILE.exists() or os.path.getsize(UPLOAD_FILE) == 0:
        return False
    
    logger.info("New user data detected, starting processing...")
    
    # Process the upload
    if not run_script("process_upload"):
        logger.error("Failed to process uploads")
        return False
    
    # Process new data
    if not run_script("process_new_data"):
        logger.error("Failed to process new data")
        return False
    
    return True

def retrain_model(model_name):
    """Retrain the specified model."""
    script_name = f"train_model_{model_name.lower()[-1]}"  # Gets 'a' or 'b' from model name
    logger.info(f"Retraining {model_name}...")
    
    # Run the training script
    if run_script(script_name):
        # Update the last retrain time
        counters = load_counters()
        counters[f'last_retrain_{model_name.lower()[-1]}'] = datetime.now().isoformat()
        counters[f'model_{model_name.lower()[-1]}'] = 0  # Reset counter
        save_counters(counters)
        
        # Generate new predictions
        if run_script("churn_prediction"):
            # Generate new explanations
            run_script("explainableAI")
            return True
    
    return False

def check_retrain_conditions():
    """Check if models need to be retrained based on data thresholds."""
    counters = load_counters()
    
    # Check data-based conditions for Model A
    if counters.get('model_a', 0) >= FREQ_MODEL_A:
        logger.info(f"Data threshold reached for Model A ({counters['model_a']} >= {FREQ_MODEL_A}), retraining...")
        retrain_model('model_a')
    
    # Check data-based conditions for Model B
    if counters.get('model_b', 0) >= FREQ_MODEL_B:
        logger.info(f"Data threshold reached for Model B ({counters['model_b']} >= {FREQ_MODEL_B}), retraining...")
        retrain_model('model_b')

def main():
    logger.info("Starting automated pipeline...")
    
    # Initial setup
    os.makedirs(DATASET_DIR, exist_ok=True)
    
    # Schedule regular checks (in seconds)
    schedule.every(CHECK_INTERVAL).seconds.do(check_for_new_data)
    schedule.every(60).seconds.do(check_retrain_conditions)  # Check retrain conditions every minute
    
    logger.info("Pipeline is running. Press Ctrl+C to exit.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
    finally:
        logger.info("Pipeline shutdown complete")

if __name__ == "__main__":
    main()
