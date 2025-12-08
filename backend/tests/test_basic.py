import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.database import db_service

def test_db():
    print("Testing Database Service...")
    schema = db_service.get_schema()
    print("Schema retrieved:")
    print(schema)
    
    if "Table: patients" not in schema:
        print("FAIL: Patients table not found.")
        sys.exit(1)
        
    print("\nExecuting sample query...")
    results = db_service.execute_query("SELECT * FROM patients LIMIT 5")
    print(f"Row count: {results['row_count']}")
    
    if results['row_count'] != 5:
        print("FAIL: Expected 5 rows.")
        sys.exit(1)
        
    print("PASS: Database Service works.")

if __name__ == "__main__":
    test_db()
