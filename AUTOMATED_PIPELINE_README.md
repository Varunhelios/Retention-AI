# Automated Model Training Pipeline

This document describes the automated pipeline for processing new user data and retraining the churn prediction models.

## Overview

The automated pipeline monitors for new user data, processes it, and triggers model retraining based on configurable conditions. The pipeline consists of several components that work together to keep the models up-to-date.

## Components

### 1. `automated_pipeline.py`

The main script that orchestrates the entire process. It:
- Monitors for new user uploads
- Triggers data processing
- Manages model retraining schedules
- Handles logging and error reporting

### 2. `process_upload.py`
- Processes new user data from `user-uploads.csv`
- Appends data to the main dataset
- Maintains data consistency

### 3. `process_new_data.py`
- Splits the dataset for model training
- Updates training counters
- Triggers model retraining when thresholds are met

### 4. Model Training Scripts
- `train_model_a.py`: Trains the XGBoost model
- `train_model_b.py`: Trains the Random Forest model with sentiment analysis
- `churn_prediction.py`: Combines predictions from both models

## Configuration

### File Locations
- **Input Data**: `datasets/user-uploads.csv`
- **Main Dataset**: `datasets/main-dataset.csv`
- **Models**: `models/`
- **Logs**: `pipeline.log`

### Environment Variables
Create a `.env` file in the root directory with the following variables:
```
LOG_LEVEL=INFO
CHECK_INTERVAL=5
MODEL_A_RETRAIN_INTERVAL=60
MODEL_B_RETRAIN_INTERVAL=30
FREQ_MODEL_A=20
FREQ_MODEL_B=10
```

## Usage

### Starting the Pipeline
```bash
# From the project root directory
python scripts/automated_pipeline.py
```

### Adding New Data
1. Place new user data in `datasets/user-uploads.csv`
2. The pipeline will automatically detect and process the new data
3. Models will be retrained based on the configured conditions

### Monitoring
- Check `pipeline.log` for detailed logs
- The script outputs status messages to the console
- Training counters are stored in `datasets/training_counters.json`

## Retraining Logic

### Time-based Retraining
- Model A: Every 60 minutes
- Model B: Every 30 minutes

### Data-based Retraining
- Model A: After 20 new records
- Model B: After 10 new records

## Error Handling
- Failed processing attempts are logged
- The pipeline continues running after errors
- Check `pipeline.log` for troubleshooting

## Dependencies
- Python 3.7+
- Required packages (install with `pip install -r requirements.txt`):
  - pandas
  - schedule
  - python-dotenv
  - scikit-learn
  - xgboost
  - nltk (for sentiment analysis)

## Troubleshooting

### Common Issues
1. **Missing Dependencies**: Install required packages
2. **File Permissions**: Ensure the script has write access to the datasets and models directories
3. **Corrupted Data**: Check the logs for data validation errors
4. **Model Training Failures**: Verify the training data format and content

### Logs
All operations are logged to `pipeline.log` with timestamps and log levels (DEBUG, INFO, WARNING, ERROR).
