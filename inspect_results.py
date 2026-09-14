import os
import json
import glob
from collections import Counter
from urllib.parse import urlparse


def newest_file():
    """Finds the most recent raw results file."""
    files = glob.glob(os.path.join("data", "raw_results_*.json"))

    if not files:
        return None

    return max(files, key=os.path.getmtime)


def main():
    path = newest_file()

    if not path:
        print("No results file found. Run search_runner.py first.")
        return

    with open(path, "r", encoding="utf-8") as handle:
        results = json.load(handle)

    print(f"File: {path}")
    print(f"Total links: {len(results)}")
    print()

    # Which websites are giving us the most links
    domains = Counter()

    for item in results:
        host = urlparse(item["link"]).netloc.replace("www.", "")
        domains[host] += 1

    print("TOP 25 DOMAINS")
    print("-" * 50)

    for host, count in domains.most_common(25):
        print(f"{count:>4}  {host}")

    print()

    # Links that several different queries turned up
    multi = [r for r in results if len(r["found_by"]) >= 3]
    multi.sort(key=lambda r: len(r["found_by"]), reverse=True)

    print(f"FOUND BY 3+ QUERIES ({len(multi)} links)")
    print("-" * 50)

    for item in multi[:15]:
        print(f"[{len(item['found_by'])}x] {item['title']}")
        print(f"      {item['link']}")

    print()

    # How many carry a date from the source
    dated = sum(1 for r in results if r.get("source_date"))
    print(f"Links with a date attached: {dated} of {len(results)}")


if __name__ == "__main__":
    main()