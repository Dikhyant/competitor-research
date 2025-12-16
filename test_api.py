"""
Test script for the competitors API endpoint.
"""
import requests
import json
import time

# Wait a moment for server to be ready
time.sleep(5)

url = "http://localhost:8000/api/competitors/"
company_url = "https://www.harveynichols.com/"

print(f"Testing API endpoint: {url}")
print(f"Company URL: {company_url}")
print("-" * 50)

# Test POST request
try:
    response = requests.post(
        url,
        json={"url": company_url},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the server. Make sure Django server is running on http://localhost:8000")
except Exception as e:
    print(f"Error: {str(e)}")
    if hasattr(e, 'response'):
        print(f"Response: {e.response.text}")

