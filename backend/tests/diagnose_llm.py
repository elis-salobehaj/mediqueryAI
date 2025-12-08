import sys
import os

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd()))

from services.database import db_service
from services.llm_agent import llm_agent
from dotenv import load_dotenv
import google.generativeai as genai

# Load env explicitly
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {bool(api_key)}")

# Configure Agent
if api_key:
    llm_agent.configure(api_key)

print("\n--- CHECKING SCHEMA ---")
try:
    schema = db_service.get_schema()
    print(f"Schema Length: {len(schema)}")
    # print(f"Schema Preview:\n{schema[:500]}...")
    if "Table:" not in schema or "state" not in schema:
        print("WARNING: Schema might likely missing 'state' or 'tables'.")
        print(f"Full Schema: {schema}")
except Exception as e:
    print(f"Schema Error: {e}")

print("\n--- CHECKING LLM GENERATION ---")
try:
    test_query = "Count patients by state"
    print(f"Testing Query: '{test_query}'")
    
    # Direct access to verify internals
    if not llm_agent.model:
        print("ERROR: Agent model not initialized.")
    else:
        sql = llm_agent.generate_sql(test_query, schema)
        print(f"Generated SQL: {sql}")
        
        if sql == "NO_MATCH" or sql is None:
             print("LLM returned NO_MATCH or None.")
except Exception as e:
    print(f"LLM Error: {e}")
