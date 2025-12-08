import requests
import json
import sys

def test_query():
    url = "http://localhost:8000/query"
    payload = {
        "question": "analyze patient demographics",
        "model_id": "gemini-1.5-pro"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        print("\nSuccess! Response received:")
        print(f"Insight: {data.get('insight', 'No insight')}")
        print(f"SQL: {data.get('sql', 'No SQL')}")
        
        if data.get('data'):
            print(f"Data Rows: {len(data['data'])}")
            print("First row:", data['data'][0])
        else:
            print("No data returned.")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to backend. Is uvicorn running?")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if 'response' in locals():
            print("Response text:", response.text)
        sys.exit(1)

if __name__ == "__main__":
    test_query()
