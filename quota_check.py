import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    client.models.generate_content(model="gemini-3.6-flash", contents="hi")
    print("gemini-3.6-flash: OK right now")
except Exception as error:
    print("gemini-3.6-flash error:")
    print(str(error)[:1500])

print("\nFlash models on this key:")
for model in client.models.list():
    if "flash" in model.name:
        print(" ", model.name)