"""Sorts raw search links into three buckets before any AI runs.

  skip    - directories, aggregators, job boards, listicles.
  snippet - social links. Use Google's snippet text, never fetch.
  fetch   - real pages worth downloading in full.

Note: a bare homepage is NOT skipped. In Nigeria big events often
have their own domain, so the homepage is the event page.
"""

import os
import json
import glob
from urllib.parse import urlparse

# Aggregators, directories, job boards, listicles.
# These never describe one specific event with one organiser.
SKIP_DOMAINS = {
    # event directories
    "10times.com",
    "allevents.in",
    "eventalways.com",
    "eventsize.com",
    "stayhappening.com",
    "shows.ng",
    "myzentroapp.com",
    "jantareview.com",
    "nigeria.jantareview.com",
    "igbadun.com.ng",
    # conference alert spam
    "conferencealerts.co.in",
    "conferencealerts.com",
    "allconferencealert.com",
    "allconferencealert.net",
    "internationalconferencealerts.com",
    "conferencenext.com",
    "philevents.org",
    "dev.events",
    # music listing
    "songkick.com",
    "detour.songkick.com",
    "bandsintown.com",
    "open.spotify.com",
    "shazam.com",
    "ticketmaster.com",
    # trade fair directories
    "tradefairdates.com",
    "tradeindia.com",
    "expoassist.net",
    "cantonfair.net",
    "constructafrica.com",
    "ensun.io",
    # travel and tourism
    "tripadvisor.com",
    "expedia.com",
    "trip.com",
    "qa.trip.com",
    "cvent.com",
    "tourradar.com",
    "mindtrip.ai",
    "timeanddate.com",
    "worldtravelguide.net",
    "twinkl.com.ng",
    # business directories and listicles
    "finelib.com",
    "clutch.co",
    "sortlist.com",
    "topseos.com",
    "techbehemoths.com",
    "ranked.ng",
    "businesslist.com.ng",
    "starofservice.com.ng",
    "babymigo.com",
    "joyribbons.com",
    "rentechdigital.com",
    "anyservice.ng",
    "takooka.com",
    "viscorner.com",
    "savycon.com",
    "connectnigeria.com",
    "trustamai.com",
    "flipbz.org",
    "yellowlyfe.com",
    "malhub.org",
    "jiji.ng",
    "nigeriapropertycentre.com",
    "s-soundspro.com",
    "clickate.com",
    # job boards
    "indeed.com",
    "ng.indeed.com",
    "glassdoor.com",
    "jooble.org",
    "ng.jooble.org",
    "whatjobs.com",
    "en-ng.whatjobs.com",
    # general noise
    "youtube.com",
    "tiktok.com",
    "en.wikipedia.org",
    "wikipedia.org",
    "scribd.com",
    "archive.org",
    "nairaland.com",
    "msn.com",
    "scholarshipair.com",
    "adventistyearbook.org",
}

# Social platforms. Snippet only, the page is behind a wall.
SNIPPET_DOMAINS = {
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "threads.com",
    "threads.net",
    "linkedin.com",
    "ng.linkedin.com",
}

# Listing-page paths. Only skipped on sites that also host real pages.
SKIP_PATTERNS = [
    "/d/nigeria",      # eventbrite discovery
    "/b/nigeria",      # eventbrite browse
    "/discover/city",
    "/search",
    "/category/",
    "/categories/",
    "/tag/",
    "/events-in-",
    "/things-to-do",
    "/jobs",
]


def get_host(link):
    return urlparse(link).netloc.replace("www.", "").lower()


def classify(item):
    """Returns one of: skip, snippet, fetch."""
    link = item.get("link", "")
    host = get_host(link)
    path = urlparse(link).path.lower()

    if host in SKIP_DOMAINS:
        return "skip"

    # match subdomains too, e.g. qa.trip.com
    for skip_host in SKIP_DOMAINS:
        if host.endswith("." + skip_host):
            return "skip"

    if host in SNIPPET_DOMAINS:
        return "snippet"

    for pattern in SKIP_PATTERNS:
        if pattern in path:
            return "skip"

    return "fetch"


def newest_file():
    files = glob.glob(os.path.join("data", "raw_results_*.json"))
    return max(files, key=os.path.getmtime) if files else None


def main():
    path = newest_file()

    if not path:
        print("No results file found. Run search_runner.py first.")
        return

    with open(path, "r", encoding="utf-8") as handle:
        results = json.load(handle)

    buckets = {"skip": [], "snippet": [], "fetch": []}

    for item in results:
        item["bucket"] = classify(item)
        buckets[item["bucket"]].append(item)

    total = len(results)

    print(f"File: {path}")
    print(f"Total links: {total}")
    print()
    print("BUCKETS")
    print("-" * 50)

    for name in ("skip", "snippet", "fetch"):
        count = len(buckets[name])
        share = (count / total * 100) if total else 0
        print(f"{name:>8}  {count:>4}  ({share:.0f}%)")

    print()
    print("SAMPLE OF 'fetch' (these get downloaded)")
    print("-" * 50)

    for item in buckets["fetch"][:20]:
        print(f"  {item['title'][:65]}")
        print(f"    {item['link'][:90]}")

    print()
    print("SAMPLE OF 'skip' (check we are not losing good leads)")
    print("-" * 50)

    for item in buckets["skip"][:20]:
        print(f"  {item['title'][:65]}")
        print(f"    {item['link'][:90]}")

    outfile = os.path.join("data", "classified.json")

    with open(outfile, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)

    print()
    print(f"Saved to: {outfile}")


if __name__ == "__main__":
    main()