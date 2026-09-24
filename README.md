# Event Lead Generation System

Finds upcoming Nigerian events that will need stage, truss, LED screens, lighting or sound, works out who is organising them, pulls their public contact details, scores each opportunity and delivers a ready to work spreadsheet.

Built for an event production, rental and installation business covering Lagos, Ogun, Oyo, Osun and Kwara.

---

# Part 1: For the business team

You do not need to touch any code to use this. Read this part only.

## What you get

A spreadsheet with four tabs. The tabs are at the bottom left of the Excel window.

| Tab                    | What is in it                                                                     |
| ---------------------- | --------------------------------------------------------------------------------- |
| **Summary**            | Headline numbers from the run                                                     |
| **Event Leads**        | Upcoming events with a confirmed date, best first                                 |
| **Company Leads**      | Agencies, production companies and venues worth a relationship                    |
| **Date Not Confirmed** | Events where the date could not be confirmed. Check these, do not prioritise them |

## Reading the Event Leads tab

Rows are sorted best first. The Priority column is colour coded.

| Priority     | Score     | What it means               |
| ------------ | --------- | --------------------------- |
| **Hot**      | 80 to 100 | Call this week              |
| **Strong**   | 60 to 79  | Worth a proposal            |
| **Research** | 40 to 59  | Needs a look before calling |
| **Low**      | under 40  | Only if you have spare time |

The columns, left to right:

- **Event, Type, Date, Days Away** — what it is and when
- **Venue, City, State** — where
- **Organiser, Organiser Type** — who is running it, and whether they are a brand, an agency, a church, a university and so on
- **Email, Phone** — public business contact, blank if none was published
- **Verify Contact** — if this says **Verify**, the email may belong to the venue or the website the event was listed on, not the organiser. Check before sending anything.
- **Website** — the organiser's own site
- **Likely Needs** — what production the event will probably require
- **Scale** — rough size
- **Summary** — one line describing the opportunity
- **Sources** — how many places this event was found. More than one usually means a bigger event.
- **Link** — click it. This is where the event was found. Every lead can be verified.
- **Status, Notes** — yours to fill in

## How your team should work it

1. Sort or filter by **Priority**, start at Hot
2. For each lead, click the **Link** and confirm it is real
3. If the Email is blank, use the Link and the Website to find a contact
4. Put **Called**, **Proposal sent**, **Won** or **Lost** in the **Status** column
5. If a lead is rubbish, write why in **Notes**

Step 5 matters more than it looks. Those notes are how the system gets better. Send the marked up sheet back after each round.

## Why some leads have no contact

Around 40 out of every 100 events have a public email or phone. Many Nigerian organisers publish only an Instagram handle, or nothing at all.

The system will never invent a contact. A blank means nothing was published, not that nobody looked. The Link gives your team a five minute head start on finding one.

## Where the leads come from

Google, Nigerian news sites, ticketing platforms like Tix Africa and Eventbrite, conference and trade fair listings, company and agency websites, chamber of commerce pages and university announcement pages.

Instagram and Facebook posts are picked up indirectly, through Google. Those platforms do not allow automated searching of public posts, so coverage there is partial.

## What it looks for

Not just events that are already public knowledge. It watches for early signals:

- Event, tour and campus tour announcements
- Save the date and coming soon posts
- Ticket and registration pages going live
- Venue and sponsorship announcements
- Brand activations and product launches
- Calls for vendors, exhibitors and event partners

The aim is to reach the organiser while they are still choosing suppliers.

---

# Part 2: For whoever runs it

## What happens, in order

```
queries.py        builds 106 search queries from a city list and a template list
search_runner.py  runs them through Serper, collects unique links
classify.py       sorts links into skip / snippet / fetch
fetcher.py        downloads pages, strips navigation, grabs emails and phones
prepare.py        builds the AI input and estimates cost
extract.py        AI reads each item, returns structured JSON
export_leads.py   scores, deduplicates, writes the Excel file
```

Helper scripts:

- `inspect_results.py` — which domains dominate the results
- `check_text.py` — page text quality, and which sites came back empty
- `gemini_test.py` — runs extraction on five deliberately tricky items
- `search_test.py` — one search, confirms the Serper key works
- `quota_check.py` — shows the AI daily limit and available models

## The three buckets

Not every link deserves the same treatment.

| Bucket    | What it is                                     | Action                                                     |
| --------- | ---------------------------------------------- | ---------------------------------------------------------- |
| `skip`    | Directories, job boards, conference alert spam | Ignored, costs nothing                                     |
| `snippet` | Instagram, Facebook, X, LinkedIn               | Use Google's snippet only, the page is behind a login wall |
| `fetch`   | Event pages, company sites, news               | Download the full page                                     |

The snippet bucket is more useful than it sounds. A typical one reads:

> November 22, 2026 Balmoral Convention Centre, Federal Palace Hotel, Victoria Island, Lagos.

Date, venue and city, with no scraping needed.

## Setup

Python 3.11 or newer.

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1          # Windows PowerShell
source venv/bin/activate             # Mac and Linux

pip install requests python-dotenv beautifulsoup4 lxml google-genai openpyxl
```

Create a `.env` file in the project root:

```
SERPER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

- Serper key: **serper.dev**, 2,500 free searches, no card needed
- Gemini key: **aistudio.google.com/apikey**, free tier, no card needed

On Windows, write `.env` as UTF-8. PowerShell's `>` redirect saves UTF-16 and Python cannot read it. Use:

```powershell
Add-Content -Path .env -Value "SERPER_API_KEY=xxx" -Encoding utf8
```

## Running a full cycle

```bash
python search_runner.py    # about 2 minutes
python classify.py         # instant
python fetcher.py          # 8 to 10 minutes
python prepare.py          # instant, prints the cost estimate
python extract.py          # 15 to 20 minutes
python export_leads.py     # instant
```

The finished file lands in `output/leads_YYYY-MM-DD.xlsx`.

`extract.py` resumes. If it stops for any reason, run it again and it continues from where it left off, skipping anything already processed.

## Changing what it searches for

Everything is in `queries.py`. No other file needs touching.

- `CITIES` — the cities to cover
- `CITY_TEMPLATES` — the search patterns applied to every city
- `GENERAL_QUERIES` — one off searches, including `site:` searches that force Google to look inside a specific website

Adding a city multiplies the searches by 16, so watch the cost.

## Changing how leads are scored

In `export_leads.py`:

- `score_event` — the points for timing, contact, scale, needs, location
- `score_company` — the points for company type, contact, location
- `CORE_STATES` and `CORE_CITIES` — the home area, which earns bonus points
- `MIN_DAYS_AWAY` — events closer than this are dropped, since there is no time to supply them
- `BAD_EMAIL_DOMAINS` — news sites and platforms whose emails are never the organiser's

Events with no confirmed date are capped at Research and moved to their own sheet.

## Costs

Measured on a real run.

| Item                | Per run     | Monthly, daily runs |
| ------------------- | ----------- | ------------------- |
| Serper search       | about $0.11 | about $3            |
| AI extraction       | about $0.57 | about $17           |
| Server and database |             | about $8            |
| **Total**           |             | **about $28**       |

The monthly AI figure is a ceiling. Most links repeat day to day, so after the first run only genuinely new items cost anything.

## The free tier limit

The Gemini free tier allows only **20 requests per day, per model**. A full run of 526 items needs roughly 66 requests at 8 items each.

`extract.py` works around this by rotating through nine Gemini models, since each has its own separate daily allowance. That is enough for one full run per day, with little room to spare.

For daily automated runs this needs to move to paid. Roughly $17 a month, and it removes the limits, the rotation and the free tier data sharing.

---

# Known issues

**Agencies were nearly lost.** The first version of the prompt rejected anything that was not a specific event, which threw away every agency and production company. Those are among the best leads. Fixed by adding a `company` lead type. Worth remembering if the prompt is ever rewritten.

**JavaScript sites return empty.** All tix.africa pages, plus devfestlagos.com, iih.ng, ogundigitalsummit.com and others load their content after the page loads, so the fetcher gets an empty shell. Fix is Playwright, or falling back to the Google snippet.

**Contact rate is about 40%.** Expected, not a bug. See the business section above.

**Raw HTML is not saved.** Only processed text is stored, so improvements to the text cleaner cannot be applied to old data without re-fetching.

**Foreign Lagos.** Lagos is also a town in Portugal. Searches pick up algarvecircle.com and similar. The AI filter catches these, but they will keep appearing.

**Wrong year on undated posts.** When a social post says "March 11th" with no year, the AI sometimes guesses the wrong one. Check any date that looks surprisingly far out.

---

# Not built yet

- Automatic daily runs on a server
- Daily email digest of new leads only
- Shared Google Sheet instead of a downloaded file
- WhatsApp alerts for Hot leads, which needs a Meta Business account and approved templates
- A track for buyers rather than renters: tenders, new event centres, auditorium and church building projects
- Skipping links already processed in earlier runs, so daily runs only pay for new items

---

# Data protection

The system collects only business contact details that organisations have already published publicly for business purposes. Every lead stores the source URL it came from, so any entry can be verified or deleted on request. No personal data of private individuals is collected.

Nigeria's Data Protection Act applies to storing names, emails and phone numbers. Retention rules and a removal process should be documented before this runs automatically.

The free AI tier allows the provider to use submitted text for training. Before going live with real contact data, move to a paid tier.

---

# Notes for whoever works on this next

- Do not name a file `inspect.py`. Python has a module by that name and it breaks BeautifulSoup.
- The fetcher pauses 1 to 2.5 seconds between requests on purpose. Leave it.
- Output tokens cost about four times input tokens. To cut the AI bill, shorten what the model writes back, not what it reads.
- `.env`, `data/` and `output/` are gitignored. The output file contains real contact details and must never be committed.
