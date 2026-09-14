"""Checks the quality of the fetched page text before we spend money on AI."""

import os
import json
from urllib.parse import urlparse


def main():
    path = os.path.join("data", "fetched.json")

    if not os.path.exists(path):
        print("No fetched.json found. Run fetcher.py first.")
        return

    with open(path, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    fetched = [i for i in items if i.get("page_text") is not None]

    empty = [i for i in fetched if len(i.get("page_text", "")) < 300]
    usable = [i for i in fetched if len(i.get("page_text", "")) >= 300]

    print(f"Pages fetched:     {len(fetched)}")
    print(f"Too short (<300):  {len(empty)}")
    print(f"Usable:            {len(usable)}")
    print()

    print("EMPTY OR NEAR EMPTY (these need a browser, or use snippet instead)")
    print("-" * 60)

    for item in empty[:15]:
        host = urlparse(item["link"]).netloc.replace("www.", "")
        size = len(item.get("page_text", ""))
        print(f"  {size:>5} chars  {host}")

    print()
    print("SAMPLE OF A GOOD PAGE")
    print("-" * 60)

    if usable:
        sample = usable[0]
        print(f"Title:  {sample['title']}")
        print(f"Link:   {sample['link']}")
        print(f"Emails: {sample.get('page_emails')}")
        print(f"Phones: {sample.get('page_phones')}")
        print()
        print("First 700 characters of text:")
        print(sample["page_text"][:700])

    print()
    print("SAMPLE OF A SOCIAL SNIPPET (no page fetch, snippet only)")
    print("-" * 60)

    social = [i for i in items if i.get("bucket") == "snippet"]

    for item in social[:3]:
        print(f"  {item['title'][:60]}")
        print(f"    {item.get('snippet')}")
        print()


if __name__ == "__main__":
    main()