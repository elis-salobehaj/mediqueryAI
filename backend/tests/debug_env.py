import os
from config import settings

gemini_key = settings.gemini_api_key
anthropic_key = settings.anthropic_api_key
use_local = str(settings.use_local_model)

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
if settings.use_local_model:
    print(" -> Local mode is ENABLED. Cloud keys might be skipped.")
    print(f" -> Local Model Name: {settings.local_model_name}")
    print(f" -> Ollama Host: {settings.ollama_host}")
