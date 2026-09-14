"""Builds the text we will send to the AI, and estimates the cost first."""

import os
import json

MIN_CHARS = 120
MAX_CHARS = 4000

# Claude Haiku 4.5 via the Batch API (50% off standard rates)
INPUT_PER_MILLION = 0.50
OUTPUT_PER_MILLION = 2.50
EXPECTED_OUTPUT_TOKENS = 350


def build_text(item):
    """Returns the best available text for this item, or None."""
    title = item.get("title") or ""
    snippet = item.get("snippet") or ""
    page = item.get("page_text") or ""

    parts = [f"TITLE: {title}"]

    if snippet:
        parts.append(f"SEARCH SNIPPET: {snippet}")

    # Page text only if it is actually substantial
    if len(page) >= 300:
        parts.append(f"PAGE TEXT: {page[:MAX_CHARS]}")

    emails = item.get("page_emails") or []
    phones = item.get("page_phones") or []

    if emails:
        parts.append(f"EMAILS FOUND ON PAGE: {', '.join(emails)}")

    if phones:
        parts.append(f"PHONES FOUND ON PAGE: {', '.join(phones)}")

    text = "\n".join(parts)

    if len(text) < MIN_CHARS:
        return None

    return text


def main():
    path = os.path.join("data", "fetched.json")

    if not os.path.exists(path):
        print("No fetched.json found. Run fetcher.py first.")
        return

    with open(path, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    ready = []
    dropped = 0

    for item in items:
        if item.get("bucket") == "skip":
            continue

        text = build_text(item)

        if not text:
            dropped += 1
            continue

        ready.append({
            "link": item["link"],
            "title": item.get("title"),
            "bucket": item.get("bucket"),
            "source_date": item.get("source_date"),
            "discovered_at": item.get("discovered_at"),
            "found_by": item.get("found_by", []),
            "page_emails": item.get("page_emails", []),
            "page_phones": item.get("page_phones", []),
            "input_text": text,
        })

    # Rough token estimate: 1 token is about 4 characters
    total_chars = sum(len(r["input_text"]) for r in ready)
    input_tokens = total_chars / 4
    output_tokens = len(ready) * EXPECTED_OUTPUT_TOKENS

    input_cost = (input_tokens / 1_000_000) * INPUT_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PER_MILLION
    total_cost = input_cost + output_cost

    by_bucket = {}
    for r in ready:
        by_bucket[r["bucket"]] = by_bucket.get(r["bucket"], 0) + 1

    print(f"Ready to extract:  {len(ready)}")
    print(f"Dropped (no text): {dropped}")
    print()

    for bucket, count in sorted(by_bucket.items()):
        print(f"  {bucket:>8}: {count}")

    print()
    print("COST ESTIMATE (Claude Haiku 4.5, batch pricing)")
    print("-" * 50)
    print(f"Input tokens:   ~{input_tokens:,.0f}")
    print(f"Output tokens:  ~{output_tokens:,.0f}")
    print(f"Input cost:     ${input_cost:.3f}")
    print(f"Output cost:    ${output_cost:.3f}")
    print(f"TOTAL:          ${total_cost:.3f}")
    print()
    print(f"Per run at this size, roughly ${total_cost:.2f}")
    print(f"Daily for a month:            ${total_cost * 30:.2f}")

    outfile = os.path.join("data", "to_extract.json")

    with open(outfile, "w", encoding="utf-8") as handle:
        json.dump(ready, handle, indent=2, ensure_ascii=False)

    print()
    print(f"Saved to: {outfile}")


if __name__ == "__main__":
    main()