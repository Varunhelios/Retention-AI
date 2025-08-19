import requests

def test_cors():
    url = "http://localhost:8000/api/user/1001/explanation"
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    }
    
    # Test OPTIONS (preflight) request
    print("Testing OPTIONS request...")
    response = requests.options(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    # Test GET request
    print("\nTesting GET request...")
    response = requests.get(url, headers={"Origin": "http://localhost:3000"})
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    try:
        print("\nResponse JSON:", response.json())
    except:
        print("\nNo JSON response")

if __name__ == "__main__":
    test_cors()
