import requests
import json
import sys

def test_switching():
    url = "http://localhost:8000/query"
    
    models = ["gemini-flash-latest", "gemma-3-27b-it"]
    
    for model in models:
        print(f"\nTesting Model: {model}")
        payload = {
            "question": "analyze patient demographics",
            "model_id": model
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            print(f"Success! Insight Length: {len(data.get('insight', ''))}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_switching()
