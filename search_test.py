import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SERPER_API_KEY")

if not API_KEY:
    print("No API key found. Check your .env file.")
    exit()

query = "concert Lagos Nigeria 2026 announcement"

response = requests.post(
    "https://google.serper.dev/search",
    headers={
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
    },
    json={
        "q": query,
        "gl": "ng",
        "num": 10,
    },
    timeout=30,
)

print("Status code:", response.status_code)

if response.status_code != 200:
    print("Something went wrong:")
    print(response.text)
    exit()

data = response.json()
results = data.get("organic", [])

print(f"Found {len(results)} results for: {query}")
print("-" * 50)

for item in results:
    print(item.get("title"))
    print(item.get("link"))
    print()