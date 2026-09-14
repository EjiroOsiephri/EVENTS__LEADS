import os
import json
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from queries import build_queries

load_dotenv()

API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

# Pause between requests so we stay polite
DELAY_SECONDS = 1


def run_one_search(query):
    """Runs a single query and returns its organic results."""
    try:
        response = requests.post(
            SERPER_URL,
            headers={
                "X-API-KEY": API_KEY,
                "Content-Type": "application/json",
            },
            json={"q": query, "gl": "ng", "num": 10},
            timeout=30,
        )
    except requests.RequestException as error:
        print(f"  network error: {error}")
        return []

    if response.status_code != 200:
        print(f"  failed ({response.status_code}): {response.text[:120]}")
        return []

    return response.json().get("organic", [])


def main():
    if not API_KEY:
        print("No API key found. Check your .env file.")
        return

    queries = build_queries()
    print(f"Running {len(queries)} queries...\n")

    # Keyed by link so duplicates collapse automatically
    found = {}
    failed = 0

    for index, query in enumerate(queries, start=1):
        print(f"[{index}/{len(queries)}] {query}")

        results = run_one_search(query)

        if not results:
            failed += 1

        for item in results:
            link = item.get("link")

            if not link:
                continue

            if link in found:
                # Already seen. Just record that this query found it too.
                found[link]["found_by"].append(query)
                continue

            found[link] = {
                "title": item.get("title"),
                "link": link,
                "snippet": item.get("snippet"),
                "source_date": item.get("date"),
                "found_by": [query],
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }

        time.sleep(DELAY_SECONDS)

    os.makedirs("data", exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    outfile = os.path.join("data", f"raw_results_{stamp}.json")

    with open(outfile, "w", encoding="utf-8") as handle:
        json.dump(list(found.values()), handle, indent=2, ensure_ascii=False)

    print()
    print("-" * 50)
    print(f"Queries run:      {len(queries)}")
    print(f"Queries failed:   {failed}")
    print(f"Unique links:     {len(found)}")
    print(f"Saved to:         {outfile}")


if __name__ == "__main__":
    main()