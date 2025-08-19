import requests
import json

# Test with different user IDs
user_ids = ["1001", "1002", "1003"]
base_url = "http://localhost:8000"  # Update if your backend runs on a different port

for user_id in user_ids:
    try:
        print(f"\n=== Testing User ID: {user_id} ===")
        
        # Get user explanation
        response = requests.get(f"{base_url}/api/user/{user_id}/explanation")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"User ID: {data.get('user_id')}")
        print(f"Churn Probability: {data.get('churn_probability')}%")
        print(f"Risk Level: {data.get('risk_level')}")
        
        print("\nTop Factors:")
        for factor in data.get('top_factors', []):
            print(f"- {factor['feature']}: {factor['value']} (Impact: {factor['impact']*100:.0f}%)")
            
        print("\nRecommendations:")
        for i, rec in enumerate(data.get('recommendations', []), 1):
            print(f"{i}. {rec}")
            
    except Exception as e:
        print(f"Error testing user {user_id}: {str(e)}")
