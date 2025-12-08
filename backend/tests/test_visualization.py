import requests
import time

def test_vis():
    url = "http://localhost:8000/query"
    
    # Test Map
    print("Testing Map Detection...")
    payload_map = {"question": "Count patients by state", "model_id": "gemma-3-27b-it"}
    try:
        res = requests.post(url, json=payload_map)
        data = res.json()
        print(f"Query: {payload_map['question']}")
        print(f"SQL: {data.get('sql')}")
        print(f"Data Keys: {data.get('data', {}).get('columns')}")
        print(f"Vis Type: {data.get('visualization_type')}")
        if data.get('visualization_type') == 'map':
            print("PASS: Map detected.")
        else:
             print(f"FAIL: Expected map, got {data.get('visualization_type')}")
    except Exception as e:
        print(f"Error: {e}")

    # Test Pie
    print("\nTesting Pie Detection...")
    payload_pie = {"question": "Show distribution of patients by gender"}
    try:
        res = requests.post(url, json=payload_pie)
        data = res.json()
        print(f"Query: {payload_pie['question']}")
        print(f"Vis Type: {data.get('visualization_type')}")
        if data.get('visualization_type') in ['pie', 'bar']: # key is distribution
            print(f"PASS: {data.get('visualization_type')} detected.")
        else:
             print(f"FAIL: Expected pie/bar, got {data.get('visualization_type')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_vis()
