import sys
import os

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd()))

from services.database import db_service
from services.llm_agent import llm_agent
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

# Load env explicitly from root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
use_local = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

print(f"Configuration Loaded:")
print(f"- Local Mode: {use_local}")
print(f"- Gemini Key: {'Present' if api_key else 'Missing'}")
print(f"- Anthropic Key: {'Present' if anthropic_key else 'Missing'}")

# Configure Agent
if api_key and not use_local:
    llm_agent.configure(api_key)

print("\n--- CHECKING SCHEMA ---")
try:
    schema = db_service.get_schema()
    print(f"Schema Length: {len(schema)}")
    if "Table:" not in schema:
        print("WARNING: Schema looks empty or malformed.")
except Exception as e:
    print(f"Schema Error: {e}")

print("\n--- CHECKING LLM GENERATION ---")
test_query = "Count patients by state"

models_to_test = []
if use_local:
    models_to_test.append("Local Ollama")
else:
    if api_key: 
        models_to_test.append("gemma-3-27b-it")
        models_to_test.append("gemini-2.5-flash-lite")
    if anthropic_key: models_to_test.append("claude-3-5-sonnet-20241022")

if not models_to_test:
    print("WARNING: No valid models found to test!")

for model_id in models_to_test:
    print(f"\nTesting Model: {model_id}")
    try:
        # Set model
        if model_id == "Local Ollama":
            pass # Already default if use_local
        else:
            llm_agent.set_model(model_id)

        # Generate
        sql = llm_agent.generate_sql(test_query, schema)
        print(f" -> Result: {sql}")
        
        if sql == "NO_MATCH" or sql is None or sql == "RATE_LIMIT":
             print(f" -> WARNING: Model returned {sql}")
        elif "SELECT" in sql.upper():
             print(" -> SUCCESS: Valid SQL generated")
    except Exception as e:
        print(f" -> ERROR: {e}")
