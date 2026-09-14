"""Tests extraction on five deliberately tricky items."""

import os
import json
import time
import logging

from dotenv import load_dotenv
from google import genai

# Silence the AFC notice
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.6-flash"

PROMPT = """You extract sales leads for a Nigerian event production company.

The company rents and sells: stage, truss, rigging, LED screens, lighting, sound.

Read the text below and return ONLY a JSON object, no markdown, no backticks.

{
  "is_relevant": true or false,
  "reject_reason": "why, or null",
  "event_name": "name or null",
  "event_type": "concert / conference / trade fair / festival / rally / church / corporate / activation / campus / awards / other",
  "start_date": "YYYY-MM-DD or null",
  "venue": "venue or null",
  "city": "city or null",
  "state": "state or null",
  "organiser": "company or person running it, or null",
  "organiser_type": "brand / agency / production company / government / church / university / other",
  "email": "business email or null",
  "phone": "phone or null",
  "website": "url or null",
  "needs": ["stage", "led", "lighting", "sound", "truss", "rigging"],
  "scale": "small / medium / large / unknown",
  "confidence": "high / medium / low"
}

Set is_relevant to FALSE if any of these are true:
- The event is not in Nigeria (watch out for Lagos in PORTUGAL)
- The event has already happened
- No specific event, just a company page or directory listing
- The event is too small to need production equipment

Today is 14 September 2026. Anything before this date has already happened.
Only guess a date if the text clearly states one. Never invent contact details.

TEXT:
"""

# Each test: a label, a string to search for, and what we expect
TESTS = [
    ("Lagos PORTUGAL trap", "algarvecircle.com", "should be REJECTED"),
    ("Past event", "osun-osogbo-2026-a-visual", "should be REJECTED (August)"),
    ("Agency page, no event", "brand-activation-agency-in-lagos", "should be REJECTED"),
    ("Trade fair", "lagosinternationaltradefair.com/", "should be KEPT"),
    ("Church convention", "Jehovah", "should be KEPT"),
]


def extract(client, text):
    response = client.models.generate_content(
        model=MODEL,
        contents=PROMPT + text,
    )

    raw = response.text.strip()
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as error:
        return None, f"{error}: {raw[:150]}"


def main():
    if not API_KEY:
        print("No GEMINI_API_KEY found in .env")
        return

    path = os.path.join("data", "to_extract.json")

    with open(path, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    client = genai.Client(api_key=API_KEY)

    for label, needle, expected in TESTS:
        match = None

        for item in items:
            haystack = item["link"] + " " + (item.get("input_text") or "")
            if needle.lower() in haystack.lower():
                match = item
                break

        print("=" * 60)
        print(f"{label}  ({expected})")
        print("=" * 60)

        if not match:
            print("  No matching item found in data, skipping.")
            print()
            continue

        print(f"  {match['title'][:70]}")
        print(f"  {match['link'][:80]}")
        print()

        result, error = extract(client, match["input_text"])

        if error:
            print(f"  PARSE FAILED: {error}")
        else:
            verdict = "KEPT" if result.get("is_relevant") else "REJECTED"
            print(f"  VERDICT:  {verdict}")

            if result.get("reject_reason"):
                print(f"  REASON:   {result['reject_reason']}")

            if result.get("is_relevant"):
                print(f"  EVENT:    {result.get('event_name')}")
                print(f"  DATE:     {result.get('start_date')}")
                print(f"  CITY:     {result.get('city')}")
                print(f"  ORGANISER:{result.get('organiser')}")
                print(f"  SCALE:    {result.get('scale')}")
                print(f"  NEEDS:    {', '.join(result.get('needs') or [])}")

        print()
        time.sleep(4)


if __name__ == "__main__":
    main()