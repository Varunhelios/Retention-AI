import requests
import json

# Test the email endpoint
url = "http://localhost:8000/api/send-retention-email"
data = {
    "email": "varunsrivatsa412@gmail.com",
    "subject": "Test Email from Retention AI",
    "message": "Hello! This is a test email from the Retention AI system.",
    "userIds": ["user123", "user456"]
}

headers = {
    "Content-Type": "application/json"
}

try:
    print("Testing email endpoint...")
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Email endpoint working!")
    else:
        print("❌ Email endpoint failed!")
        
except Exception as e:
    print(f"Error: {e}")
