import requests
import json

# Test the user explanation endpoint
response = requests.get("http://localhost:8000/api/user/1001/explanation")

print(f"Status Code: {response.status_code}")
print("Response Headers:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")

try:
    print("\nResponse JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"\nCould not parse JSON response: {e}")
    print(f"Raw response content: {response.text}")
