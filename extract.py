"""Runs AI extraction on every item.

Rotates across Gemini models, since the free tier gives each model its
own daily limit. Saves after every batch and resumes if interrupted.
"""

import os
import json
import time
import logging
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import errors

logging.getLogger("google_genai.models").setLevel(logging.ERROR)
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Tried in order. When one hits its daily limit, we move to the next.
MODELS = [
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.6-flash",
]

BATCH_SIZE = 8
PAUSE_SECONDS = 6

IN_PATH = os.path.join("data", "to_extract.json")
OUT_PATH = os.path.join("data", "extracted.json")

PROMPT = """You find sales leads for a Nigerian event production company.
It rents and sells stage, truss, rigging, LED screens, lighting and sound.
Its main area is Lagos, Ogun, Oyo, Osun, Kwara and the South West.

Today is TODAY_DATE.

You will get several ITEMS. For EACH item decide the lead_type:

event   = a specific upcoming event in Nigeria, on or after today,
          big enough to need stage, screens, lighting or sound.
company = no specific event, BUT the page is about a business worth a
          long term relationship: event agency, experiential or marketing
          agency, event production company, event centre or venue, or an
          organiser that runs events regularly. Must be in Nigeria.
reject  = anything else: past events, events outside Nigeria (Lagos in
          PORTUGAL is a trap), directories, job posts, news with no event,
          tiny private events, or not enough information.

Rules:
- Never invent emails, phones or dates. Use null if not stated.
- Emails and phones listed under FOUND ON PAGE are real, use them.
- Dates as YYYY-MM-DD. If only a month is known, use null.

Return ONLY a JSON array with one object per item, same order as the
items. No markdown. Each object has these keys:

id (the item number), lead_type, reject_reason, name, event_type,
start_date, venue, city, state, organiser, organiser_type, email, phone,
website, needs (list from: stage, led, lighting, sound, truss, rigging),
scale (small, medium, large or unknown), confidence (high, medium or low),
summary (one short sentence a salesperson can read).

For company leads, put the company name in name.

ITEMS:
"""

exhausted = set()


class AllModelsDone(Exception):
    pass


def build_batch_text(batch):
    parts = []
    for number, item in enumerate(batch, start=1):
        parts.append(f"ITEM {number}\nLINK: {item['link']}\n{item['input_text']}")
    return "\n\n".join(parts)


def call_any_model(client, prompt):
    """Tries each model in turn. Returns (text, model_name)."""
    for round_number in range(3):
        for model in MODELS:
            if model in exhausted:
                continue

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text or "", model

            except errors.ClientError as error:
                message = str(error)

                if error.code == 429 and "PerDay" in message:
                    print(f"\n    {model}: daily limit reached, switching", end="")
                    exhausted.add(model)
                    continue

                if error.code == 429:
                    print(f"\n    {model}: per minute limit, waiting 30s", end="")
                    time.sleep(30)
                    continue

                if error.code in (400, 404):
                    print(f"\n    {model}: not usable, switching", end="")
                    exhausted.add(model)
                    continue

                raise

            except errors.ServerError:
                print(f"\n    {model}: busy, trying next model", end="")
                continue

        if len(exhausted) == len(MODELS):
            raise AllModelsDone()

        print("\n    every model busy, waiting 30s", end="")
        time.sleep(30)

    raise RuntimeError("no model responded after 3 rounds")


def parse_json(raw):
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1:
        try:
            data = json.loads(cleaned[start:end + 1])
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]
        except json.JSONDecodeError:
            pass

    return None


def match_rows(batch, parsed):
    by_id = {}
    for row in parsed:
        try:
            by_id[int(row.get("id"))] = row
        except (TypeError, ValueError):
            pass

    if not by_id and len(parsed) == len(batch):
        by_id = {n: row for n, row in enumerate(parsed, start=1)}

    pairs = []
    for position, item in enumerate(batch, start=1):
        row = by_id.get(position)
        if row:
            pairs.append((item, row))
    return pairs


def attach_source(item, row, model):
    row.pop("id", None)
    row["link"] = item["link"]
    row["source_title"] = item.get("title")
    row["source_bucket"] = item.get("bucket")
    row["source_date"] = item.get("source_date")
    row["found_by_count"] = len(item.get("found_by", []))
    row["page_emails"] = item.get("page_emails", [])
    row["page_phones"] = item.get("page_phones", [])
    row["model"] = model

    if row.get("lead_type") not in ("event", "company", "reject"):
        row["lead_type"] = "reject"
    return row


def save(results):
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(list(results.values()), handle, indent=2, ensure_ascii=False)


def main():
    if not API_KEY:
        print("No GEMINI_API_KEY in .env")
        return

    with open(IN_PATH, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    results = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, "r", encoding="utf-8") as handle:
            for row in json.load(handle):
                results[row["link"]] = row

    todo = [i for i in items if i["link"] not in results]
    batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]

    print(f"Already done: {len(results)}")
    print(f"To process:   {len(todo)} items in {len(batches)} batches\n")

    client = genai.Client(api_key=API_KEY)
    prompt_head = PROMPT.replace("TODAY_DATE", date.today().strftime("%d %B %Y"))

    for number, batch in enumerate(batches, start=1):
        print(f"[batch {number}/{len(batches)}]", end=" ")

        try:
            raw, model = call_any_model(client, prompt_head + build_batch_text(batch))
        except AllModelsDone:
            print("\n\nAll free model limits used up for today.")
            break
        except Exception as error:
            print(f"\n    FAILED: {str(error)[:100]}")
            time.sleep(PAUSE_SECONDS)
            continue

        parsed = parse_json(raw)
        if not parsed:
            print(f"\n    could not parse ({model}), will retry next run")
            time.sleep(PAUSE_SECONDS)
            continue

        counts = {"event": 0, "company": 0, "reject": 0}
        for item, row in match_rows(batch, parsed):
            row = attach_source(item, row, model)
            results[item["link"]] = row
            counts[row["lead_type"]] += 1

        save(results)
        print(f"  [{model}] event {counts['event']}, "
              f"company {counts['company']}, reject {counts['reject']}")
        time.sleep(PAUSE_SECONDS)

    totals = {"event": 0, "company": 0, "reject": 0}
    for row in results.values():
        totals[row.get("lead_type", "reject")] += 1

    print("\n" + "-" * 50)
    print(f"Processed: {len(results)} of {len(items)}")
    print(f"  events:    {totals['event']}")
    print(f"  companies: {totals['company']}")
    print(f"  rejected:  {totals['reject']}")
    print(f"Saved to: {OUT_PATH}")

    if len(results) < len(items):
        print("\nSome items did not finish. Run again to continue.")


if __name__ == "__main__":
    main()