"""Downloads the pages in the 'fetch' bucket and pulls out readable text
plus any emails and phone numbers found on the page."""

import os
import re
import json
import time
import random

import requests
from bs4 import BeautifulSoup

TIMEOUT = 20
DELAY_RANGE = (1.0, 2.5)
MAX_TEXT_CHARS = 6000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Nigerian numbers: +234..., 234..., or 0803...
PHONE_RE = re.compile(
    r"(?:\+?234[\s\-]?|0)(?:7|8|9)0?\d[\s\-]?\d{3}[\s\-]?\d{4}"
)

# Emails we never want
JUNK_EMAIL_PARTS = (
    "example.com",
    "sentry.io",
    "wixpress.com",
    "godaddy.com",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    "@2x",
)


def clean_emails(text):
    found = []

    for email in EMAIL_RE.findall(text):
        low = email.lower()

        if any(junk in low for junk in JUNK_EMAIL_PARTS):
            continue

        if low not in found:
            found.append(low)

    return found[:5]


def clean_phones(text):
    found = []

    for phone in PHONE_RE.findall(text):
        digits = re.sub(r"\D", "", phone)

        # Normalise to 0XXXXXXXXXX
        if digits.startswith("234"):
            digits = "0" + digits[3:]

        if len(digits) == 11 and digits not in found:
            found.append(digits)

    return found[:5]


# Page furniture we never want
STRIP_TAGS = ["script", "style", "noscript", "svg", "nav", "header",
              "footer", "form", "aside", "iframe", "button", "select"]

# Try these in order. First one with real content wins.
CONTENT_SELECTORS = [
    "article",
    "main",
    '[role="main"]',
    ".entry-content",
    ".post-content",
    ".article-content",
    ".content",
    "#content",
]


def get_main_text(soup):
    """Returns the body text, preferring the article area over the whole page."""
    for selector in CONTENT_SELECTORS:
        block = soup.select_one(selector)

        if block:
            text = re.sub(r"\s+", " ", block.get_text(separator=" ")).strip()

            if len(text) >= 400:
                return text

    # Nothing matched, fall back to the whole body
    body = soup.body or soup
    return re.sub(r"\s+", " ", body.get_text(separator=" ")).strip()


def extract_page(html):
    soup = BeautifulSoup(html, "lxml")

    # Grab mailto links before we strip anything
    mailto = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.lower().startswith("mailto:"):
            mailto.append(href[7:].split("?")[0].strip().lower())

    # Contacts often live in the footer, so scan the full page for those
    full_soup = BeautifulSoup(html, "lxml")
    for tag in full_soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    full_text = re.sub(r"\s+", " ", full_soup.get_text(separator=" "))

    emails = clean_emails(" ".join(mailto) + " " + full_text)
    phones = clean_phones(full_text)

    # But only keep the article text for the AI
    for tag in soup(STRIP_TAGS):
        tag.decompose()

    text = get_main_text(soup)

    return text[:MAX_TEXT_CHARS], emails, phones


def main():
    path = os.path.join("data", "classified.json")

    if not os.path.exists(path):
        print("No classified.json found. Run classify.py first.")
        return

    with open(path, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    targets = [i for i in items if i.get("bucket") == "fetch"]
    print(f"Fetching {len(targets)} pages...\n")

    ok = 0
    failed = 0
    with_email = 0
    with_phone = 0

    for index, item in enumerate(targets, start=1):
        link = item["link"]
        print(f"[{index}/{len(targets)}] {link[:75]}")

        try:
            response = requests.get(link, headers=HEADERS, timeout=TIMEOUT)

            if response.status_code != 200:
                print(f"    status {response.status_code}")
                item["fetch_error"] = f"status {response.status_code}"
                failed += 1
                continue

            ctype = response.headers.get("content-type", "")

            if "html" not in ctype.lower():
                print(f"    not html ({ctype[:30]})")
                item["fetch_error"] = "not html"
                failed += 1
                continue

            text, emails, phones = extract_page(response.text)

            item["page_text"] = text
            item["page_emails"] = emails
            item["page_phones"] = phones
            ok += 1

            if emails:
                with_email += 1
            if phones:
                with_phone += 1

            note = []
            if emails:
                note.append(f"{len(emails)} email")
            if phones:
                note.append(f"{len(phones)} phone")
            if note:
                print(f"    ok, {', '.join(note)}")

        except requests.RequestException as error:
            print(f"    failed: {str(error)[:60]}")
            item["fetch_error"] = str(error)[:200]
            failed += 1

        time.sleep(random.uniform(*DELAY_RANGE))

    outfile = os.path.join("data", "fetched.json")

    with open(outfile, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2, ensure_ascii=False)

    print()
    print("-" * 50)
    print(f"Fetched ok:        {ok}")
    print(f"Failed:            {failed}")
    print(f"Pages with email:  {with_email}")
    print(f"Pages with phone:  {with_phone}")
    print(f"Saved to:          {outfile}")


if __name__ == "__main__":
    main()