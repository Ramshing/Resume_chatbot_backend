import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
print("API-key````````````````````````````````````",os.getenv("GEMINI_API_KEY"))
for m in genai.list_models():
    print(m.name, m.supported_generation_methods)
model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")