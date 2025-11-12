from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Response
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
import pandas as pd
import os
import sys
import subprocess
import json
import shutil
import joblib
import shap
import numpy as np
from pathlib import Path
import uvicorn
from pydantic import BaseModel, ConfigDict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@retentionai.com')

# Email request model
class EmailRequest(BaseModel):
    to_email: str
    subject: str
    message: str

# Initialize FastAPI app
app = FastAPI(title="Retention AI API", version="1.0.0")

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600  # 10 minutes
)

# Base directories
import os
# Get the absolute path to the project root (Retention-AI directory)
# Paths - using absolute paths to avoid any path resolution issues
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / 'datasets'
MODEL_DIR = BASE_DIR / 'models'
OUTPUTS_DIR = BASE_DIR / 'outputs'

print(f"[CONFIG] Base directory: {BASE_DIR}")
print(f"[CONFIG] Data directory: {DATA_DIR}")
print(f"[CONFIG] Model directory: {MODEL_DIR}")

# Minimal schema for uploads
REQUIRED_UPLOAD_BASE_COLUMNS = [
    'userid',
    'Average Screen Time',
    'Average Spent on App (INR)',
    'Ratings',
    'New Password Request',
    'Last Visited Minutes',
]
MIN_REQUIRED_DAY_COLUMNS = 30  # require at least 30 Day_* columns

print(f"[CONFIG] Output directory: {OUTPUTS_DIR}")

# Create output directories if they don't exist
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Ensure directories exist
for dir_path in [DATA_DIR, MODEL_DIR, OUTPUTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Pydantic models for request/response validation
class PredictionRequest(BaseModel):
    user_id: str

class FeatureImportanceResponse(BaseModel):
    features: List[Dict[str, Any]]
    chart_path: Optional[str] = None

class UserExplanationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    user_id: str
    churn_probability: float
    risk_level: str
    top_features: List[Dict[str, Any]]
    recommendations: List[str]
    chart_path: Optional[str] = None
    model_b_used: bool = False

class UploadResponse(BaseModel):
    message: str
    records_processed: int
    new_model_trained: bool

# Helper functions
def get_latest_model_path(model_name: str) -> Optional[Path]:
    """Get the path to the latest trained model."""
    model_file = MODEL_DIR / f"{model_name}_latest.pkl"
    return model_file if model_file.exists() else None

def get_feature_importance_data() -> Dict[str, Any]:
    """Calculate and return global feature importance."""
    try:
        # Load model and features
        model_path = get_latest_model_path("model_a")
        if not model_path:
            raise HTTPException(status_code=404, detail="Model not found")
            
        model = joblib.load(model_path)
        
        # Check if feature_importances_ is available
        if hasattr(model, 'feature_importances_'):
            # Load feature names
            features_path = MODEL_DIR / "model_a_features.json"
            with open(features_path) as f:
                feature_names = json.load(f)
            
            # Get feature importances
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            # Prepare response
            features = []
            for i in indices[:10]:  # Top 10 features
                features.append({
                    'name': feature_names[i],
                    'importance': float(importances[i]),
                    'rank': int(np.where(indices == i)[0][0]) + 1
                })
            
            return {
                'features': features,
                'chart_path': str(OUTPUTS_DIR / 'feature_importance.png')
            }
        else:
            # For models without feature_importances_ (e.g., logistic regression)
            return {'features': [], 'chart_path': None}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_user_explanation_data(user_id: str) -> Dict[str, Any]:
    """Load explanation for a specific user's churn prediction from pre-generated JSON."""
    try:
        # First check if we have a pre-generated explanation file
        explanation_file = OUTPUTS_DIR / 'explanations' / f'user_{user_id}.json'
        
        if not explanation_file.exists():
            # Fall back to the old method if no pre-generated file exists
            return _generate_user_explanation_data(user_id)
            
        # Load the pre-generated explanation
        with open(explanation_file, 'r') as f:
            explanation_data = json.load(f)
            
        # Ensure all required fields are present
        required_fields = ['user_id', 'churn_probability', 'risk_level', 'top_features', 'recommendations']
        if not all(field in explanation_data for field in required_fields):
            raise ValueError(f"Invalid explanation format in {explanation_file}")
            
        # Ensure we're using top_features (not top_factors)
        if 'top_factors' in explanation_data and 'top_features' not in explanation_data:
            explanation_data['top_features'] = explanation_data.pop('top_factors')
            
        # Ensure chart_path is set correctly
        if 'chart_path' not in explanation_data:
            explanation_data['chart_path'] = f"/api/user/{user_id}/chart"
            
        # Ensure model_b_used is set
        if 'model_b_used' not in explanation_data:
            explanation_data['model_b_used'] = False
            
        return explanation_data
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {explanation_file}: {str(e)}")
        return _generate_user_explanation_data(user_id)
    except Exception as e:
        print(f"[ERROR] Error loading explanation for user {user_id}: {str(e)}")
        return _generate_user_explanation_data(user_id)

def _generate_user_explanation_data(user_id: str) -> Dict[str, Any]:
    """
    Fallback method to generate explanation data if no pre-generated file exists.
    This is kept for backward compatibility.
    """
    try:
        print(f"[WARN] No pre-generated explanation found for user {user_id}, generating on the fly")
        
        # Load churn data
        churn_df = pd.read_csv(DATA_DIR / "churn_prediction.csv")
        churn_df['userid'] = churn_df['userid'].astype(str)
        user_data = churn_df[churn_df['userid'] == str(user_id)]
        
        if user_data.empty:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found in churn data")
            
        # Get basic user data
        churn_prob = float(user_data['churn_probability (%)'].iloc[0])
        risk_level = str(user_data['churn_risk'].iloc[0])
        
        # Generate a basic explanation
        explanation = {
            'user_id': user_id,
            'churn_probability': churn_prob,
            'risk_level': risk_level,
            'top_features': [],
            'recommendations': [
                "This is a fallback explanation. Pre-generated explanation not found.",
                "The system is currently using default recommendations.",
                "Please check if the explanation files were generated correctly."
            ],
            'chart_path': f"/api/user/{user_id}/chart"
        }
        
        return explanation
        
    except Exception as e:
        print(f"[ERROR] Error generating fallback explanation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation for user {user_id}: {str(e)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Error in get_user_explanation_data: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

# API Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/users")
async def get_available_users():
    """Get list of all available users with their basic info."""
    try:
        print(f"[DEBUG] Loading churn data from: {DATA_DIR / 'churn_prediction.csv'}")
        if not (DATA_DIR / "churn_prediction.csv").exists():
            raise HTTPException(status_code=500, detail="Churn prediction data not found")
            
        churn_df = pd.read_csv(DATA_DIR / "churn_prediction.csv")
        print(f"[DEBUG] Loaded {len(churn_df)} user records")
        
        # Convert to list of user objects with relevant fields
        users = []
        for _, row in churn_df.iterrows():
            try:
                users.append({
                    'user_id': str(row['userid']),
                    'churn_probability': float(row['churn_probability (%)']),
                    'risk_level': str(row['churn_risk'])
                })
            except Exception as e:
                print(f"[WARNING] Error processing row {_}: {e}")
                continue
            
        print(f"[DEBUG] Returning {len(users)} users")
        return {"data": users}  # Wrap in a data object to match frontend expectations
        
    except HTTPException as he:
        print(f"[ERROR] HTTP Error: {he.detail}")
        raise
    except Exception as e:
        import traceback
        error_msg = f"Error getting user list: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "details": str(e)})

@app.get("/api/feature-importance", response_model=FeatureImportanceResponse)
async def get_feature_importance():
    """
    Get global feature importance for the churn prediction model.
    Returns the top 10 most important features and their importance scores.
    """
    return get_feature_importance_data()

@app.get("/api/user/{user_id}/explanation", response_model=UserExplanationResponse)
async def get_user_explanation(user_id: str):
    """Get explanation for user's churn prediction."""
    try:
        print(f"[DEBUG] Getting explanation for user {user_id}")
        result = get_user_explanation_data(user_id)
        # Ensure user_id is a string in the response
        if 'user_id' in result:
            result['user_id'] = str(result['user_id'])
        print(f"[DEBUG] Successfully got explanation: {result}")
        return result
    except HTTPException as he:
        print(f"[ERROR] HTTPException in get_user_explanation: {str(he)}")
        raise he
    except Exception as e:
        import traceback
        error_msg = f"[ERROR] Unexpected error in get_user_explanation: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sentiment")
async def get_sentiment_analysis():
    """Get sentiment analysis data."""
    try:
        sentiment_file = DATA_DIR / "sentiment_analysis.csv"
        if not sentiment_file.exists():
            return JSONResponse(
                status_code=404,
                content={"message": "Sentiment data not found"}
            )
        
        df = pd.read_csv(sentiment_file)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/churn-predictions")
async def get_churn_predictions():
    """Get churn prediction data."""
    try:
        predictions_file = DATA_DIR / "churn_prediction.csv"
        if not predictions_file.exists():
            raise HTTPException(status_code=404, detail="Churn predictions not found")
        
        df = pd.read_csv(predictions_file)
        
        # Convert to the format expected by the frontend
        predictions = []
        for _, row in df.iterrows():
            predictions.append({
                "userid": str(row["userid"]),
                "churn_probability (%)": float(row["churn_probability (%)"]),
                "churn_risk": str(row["churn_risk"])
            })
        
        return {"data": predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        if not predictions_file.exists():
            raise HTTPException(status_code=404, detail="Churn predictions not found. Please ensure the model has been trained.")
        
        # Read the predictions file
        df = pd.read_csv(predictions_file)
        
        if explanation_file.exists():
            print("Found cached explanation")
            with open(explanation_file, 'r') as f:
                return json.load(f)
        
        print("No cached explanation found, generating new one...")
        # Generate explanation if not cached
        explanation = get_user_explanation_data(user_id)
        
        # Cache the explanation
        with open(explanation_file, 'w') as f:
            json.dump(explanation, f)
            
        return explanation
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_user_explanation: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/chart")
async def get_user_chart(user_id: str):
    """Get the SHAP chart for a specific user."""
    try:
        chart_path = OUTPUTS_DIR / "charts" / f"user_{user_id}.png"
        if not chart_path.exists():
            raise HTTPException(status_code=404, detail=f"Chart for user {user_id} not found")
        
        return FileResponse(str(chart_path), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _run_process_upload_script():
    """Run scripts/process_upload.py to process the uploaded CSV in background."""
    try:
        script_path = BASE_DIR / 'scripts' / 'process_upload.py'
        subprocess.run([sys.executable, str(script_path)], cwd=BASE_DIR, check=True)
    except Exception as e:
        print(f"[ERROR] Background processing failed: {e}")


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Handle file uploads for new user data."""
    try:
        # Save uploaded file
        upload_path = DATA_DIR / "user-uploads.csv"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the upload (this would trigger the automated pipeline)
        # In a real implementation, you'd call your processing scripts here
        # For now, we'll just return a success message
        
        # Validate and count records in the uploaded file
        try:
            df = pd.read_csv(upload_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")
        
        # Check required base columns
        missing = [c for c in REQUIRED_UPLOAD_BASE_COLUMNS if c not in df.columns]
        # Check Day_* columns
        day_cols = [c for c in df.columns if isinstance(c, str) and c.startswith('Day_')]
        if missing or len(day_cols) < MIN_REQUIRED_DAY_COLUMNS:
            detail = {
                "error": "Invalid upload schema",
                "missing_required_columns": missing,
                "day_columns_found": len(day_cols),
                "day_columns_required_min": MIN_REQUIRED_DAY_COLUMNS,
            }
            raise HTTPException(status_code=422, detail=detail)
        
        record_count = len(df)

        # Kick off background processing so the file doesn't stay stuck
        background_tasks.add_task(_run_process_upload_script)

        return {
            "message": "File uploaded successfully",
            "records_processed": record_count,
            "new_model_trained": False  # This would be determined by the pipeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get statistics for the dashboard."""
    try:
        # Read the churn predictions data
        predictions_file = DATA_DIR / "churn_prediction.csv"
        if not predictions_file.exists():
            return {
                "total_users": 0,
                "churn_rate": 0.0,
                "retention_rate": 0.0,
                "recent_activity": []
            }
        
        # Read the CSV file with proper error handling
        try:
            df = pd.read_csv(predictions_file)
            # Ensure we have the expected columns
            if 'userid' not in df.columns or 'churn_risk' not in df.columns:
                raise ValueError("CSV file is missing required columns")
        except Exception as e:
            print(f"Error reading churn prediction file: {e}")
            return {
                "total_users": 0,
                "churn_rate": 0.0,
                "retention_rate": 0.0,
                "recent_activity": []
            }
        
        # Calculate statistics
        total_users = df['userid'].nunique()  # Count unique users
        
        # Calculate churn rate based on high risk users
        high_risk_users = len(df[df['churn_risk'] == 'High']) if 'churn_risk' in df.columns else 0
        churn_rate = (high_risk_users / len(df)) * 100 if len(df) > 0 else 0
        retention_rate = 100 - churn_rate
        
        # Get recent activity (last 5 users with high churn risk)
        recent_activity = []
        if not df.empty and 'userid' in df.columns and 'churn_risk' in df.columns:
            recent_activity = df[df['churn_risk'] == 'High'].head(5)[['userid', 'churn_risk']].to_dict('records')
        
        # Ensure we're not returning NaN values
        churn_rate = 0.0 if pd.isna(churn_rate) else round(float(churn_rate), 2)
        retention_rate = 100.0 if pd.isna(retention_rate) else round(float(retention_rate), 2)
        
        print(f"Dashboard stats - Users: {total_users}, Churn Rate: {churn_rate}%")
        
        return {
            "total_users": int(total_users),
            "churn_rate": churn_rate,
            "retention_rate": retention_rate,
            "recent_activity": recent_activity or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Email endpoint - Note: No trailing slash to match frontend
@app.post("/api/send-retention-email")
async def send_retention_email(request: Request):
    try:
        # Log the incoming request
        body = await request.body()
        print(f"Received request with body: {body}")
        
        # Parse JSON manually to see the exact content
        try:
            data = await request.json()
            print(f"Parsed JSON data: {data}")
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
            
        # Validate required fields
        required_fields = ['to_email', 'subject', 'message']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = data['to_email']
        msg['Subject'] = data['subject']
        
        # Add message body
        msg.attach(MIMEText(data['message'], 'plain'))
        
        # Create SMTP session
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        return {"status": "success", "message": "Email sent successfully!"}
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# Serve the frontend build files
frontend_build_dir = BASE_DIR / "retention-ai-frontend" / "build"
if frontend_build_dir.exists() and frontend_build_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True), name="static")
    print(f"Serving static files from {frontend_build_dir}")
else:
    print(f"Warning: Frontend build directory not found at {frontend_build_dir}")
    print("Frontend will not be served. Please build the frontend first.")

# For development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
