import google.generativeai as genai
import os
from dotenv import load_dotenv

# Try different path for .env just in case
load_dotenv("app/.env")

api_key = os.getenv("GEMINI_API_KEY")
print(f"Using API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

genai.configure(api_key=api_key)

try:
    print("Listing ALL available models names:")
    for m in genai.list_models():
        print(f" - {m.name}")
except Exception as e:
    print(f"Error during list_models: {e}")
