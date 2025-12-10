from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (3 levels up from tests file: backend/tests/ -> backend/ -> root)
# Actually tests/ is inside backend/. So: tests -> backend -> root (2 parent jumps from backend, wait)
# root/backend/tests/debug_env.py
# parent -> backend
# parent.parent -> root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

gemini_key = os.getenv("GEMINI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
use_local = os.getenv("USE_LOCAL_MODEL", "false")

print(f"Current Working Directory: {os.getcwd()}")

# 1. Gemini
print(f"Checking GEMINI_API_KEY... Found: {'YES' if gemini_key else 'NO'}")
if gemini_key:
    if gemini_key == "YOUR_API_KEY_HERE" or "your_api_key" in gemini_key:
        print(" -> WARNING: Gemini Key is still the placeholder!")
    else:
        print(f" -> Starts with: {gemini_key[:4]}...")

# 2. Anthropic
print(f"Checking ANTHROPIC_API_KEY... Found: {'YES' if anthropic_key else 'NO'}")
if anthropic_key:
    if "your_api_key" in anthropic_key:
        print(" -> WARNING: Anthropic Key is still the placeholder!")
    else:
        print(f" -> Starts with: {anthropic_key[:4]}...")

# 3. Local Model
print(f"Checking USE_LOCAL_MODEL... Value: {use_local}")
if use_local.lower() == 'true':
    print(" -> Local mode is ENABLED. Cloud keys might be skipped.")
    print(f" -> Local Model Name: {os.getenv('LOCAL_MODEL_NAME', 'Not Set')}")
    print(f" -> Ollama Host: {os.getenv('OLLAMA_HOST', 'Not Set')}")
