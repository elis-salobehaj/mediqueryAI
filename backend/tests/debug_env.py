import os
from dotenv import load_dotenv

# Try loading from current directory
load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Loading .env... Key found: {'YES' if key else 'NO'}")
if key:
    print(f"Key starts with: {key[:4]}...")
    print(f"Key ends with: ...{key[-4:]}")
    if key == "YOUR_API_KEY_HERE":
        print("WARNING: Key is still the placeholder!")
else:
    print("ERROR: GEMINI_API_KEY not found in environment.")
