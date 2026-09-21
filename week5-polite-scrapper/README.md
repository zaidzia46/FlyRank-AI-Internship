# The polite scraper — Books to Scrape

A small, polite scraping pipeline for FlyRank Internship, Backend Track, Week 5 (A9).

## Target classification

- **Site:** [books.toscrape.com](https://books.toscrape.com)
- **Why this site:** its parent page, [toscrape.com](https://toscrape.com), states it is a
  "Web Scraping Sandbox" — a fictional bookstore that "desperately wants to be scraped," built
  specifically so people can practise and validate scraping code on it. That sentence is the
  permission for this assignment; it is the only kind of site this project touches.
- **Scope:** the first **3 catalogue pages only** (`catalogue/page-1.html` through
  `catalogue/page-3.html`, ~60 books total), plus each of those books' own detail pages.
- **Data collected:** per book — title, price, stock status, star rating, and description, all of
  which are shown in plain HTML on the page itself.
- **robots.txt result:** a request to `https://books.toscrape.com/robots.txt` returns
  **HTTP 404 — no robots file found**. A missing file is not permission on its own; the real
  permission is the sandbox's own stated purpose above.
- **Why this is appropriate here:** the site is explicitly built and offered for this exact
  purpose, the scope is tiny (3 pages / ~60 books, out of the site's ~1000), and every request
  below identifies itself, waits between requests, and stops on the first sign the site would
  rather not be asked.

**I will not reuse this code on another site without checking its rules and terms first.**

## Politeness rules (so far)

Every real request to the site:
- sends an honest **user-agent**: `FlyRankInternshipA9/1.0 (+link-to-your-repo)`
- has a 10-second **timeout** — it never waits forever
- checks the **status code** — only HTTP 200 is treated as a real page
- is saved to `cache/` — a page is asked for once; every run after that reads the saved copy

## Record shape (raw, before cleaning)

Each book page produces this raw record — nothing normalized yet:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-06T10:00:00Z"
}
```

Selectors are aimed at the product area of the page (`div.product_main`), not the whole
document. Books with no description store `null` — the code never invents text that wasn't
on the page.

## Record shape (clean, validated)

`price_text` becomes a numeric `price_gbp`, the original text is kept alongside it, and the
absolute `product_url` is each record's canonical identity — if the same book turns up twice,
it counts once. The full schema (defined once with Pydantic in `src/schema.py`):

| field | type | notes |
|---|---|---|
| `title` | string | |
| `product_url` | URL | canonical identity |
| `price_gbp` | number | normalized from `price_text` |
| `price_text` | string | original, kept for reference |
| `in_stock` | bool | |
| `stock_count` | number \| null | |
| `availability_text` | string | original |
| `rating` | number \| null | normalized from `rating_text` |
| `rating_text` | string \| null | original |
| `description` | string \| null | `null`, never invented |
| `source_page`, `fetched_at` | string | provenance |

A record that fails validation is written to `output/errors.json` with a reason and never
reaches `books.json`.

## Surviving failures

Each page is handled separately, so one broken page is logged and skipped — it never takes
the rest of the run down. A timeout or a `5xx` server error gets one retry with a short wait;
a `404` (the page doesn't exist) or `403` (the site said no) is never retried.

Every run ends with `output/run-report.json` — a few honest numbers: start time, duration,
pages fetched, cache hits, valid records, invalid records, failed pages.

## Try it

```bash
pip install -r requirements.txt
python -m src.main
```

To prove one bad page can't kill the run, add one made-up book URL on purpose:
```bash
python -m src.main --inject-broken-url
```
`output/books.json` still has the 60 good records, and `run-report.json` shows
`"failed_pages": 1`.

## How to run

```bash
git clone <your-repo-url>
cd scraper
pip install -r requirements.txt
python -m src.main
```

This produces `output/books.json` (60 records), `output/errors.json` (any that failed
validation), and `output/run-report.json`. To prove a broken page can't kill the run:

```bash
python -m src.main --inject-broken-url
```

Run the tests:
```bash
pip install pytest
python -m pytest tests/ -v
```

## Lane

Python 3.10+, using:
- `requests` for HTTP
- `beautifulsoup4` for HTML parsing
- `pydantic` for schema validation

## Politeness rules

| Rule | How |
|---|---|
| Identify yourself | `User-Agent: FlyRankInternshipA9/1.0 (+link-to-your-repo)` on every real request |
| Don't wait forever | 10-second timeout on every request |
| Go slowly | ≥0.5s delay between real requests to the site (cached pages need none) |
| Don't ask twice | every page is cached to `cache/` after its first successful fetch |
| Check the response | only HTTP 200 is treated as a real page |
| Retry only what's worth retrying | a timeout or `5xx` gets one retry; a `404` or `403` never does |

## Why this assignment needed no browser

Every field this scraper collects — title, price, availability, rating, description — is
already present in the plain HTML the server sends back for a normal `GET` request; none of
it is injected by JavaScript after the page loads. A verified `requests.get()` on
`books.toscrape.com/catalogue/page-1.html` returns the full list of 20 books, their prices,
and the link to the next page, with no browser involved. A headless browser would only add
startup and rendering cost here for zero benefit — that trade-off flips once a page's data
lives in JavaScript instead of the initial HTML (see `quotes.toscrape.com/js`, which is what
the stretch goal's browser-cost comparison demonstrates).

## Sample run

One real, verified record from `books.toscrape.com` (fetched 2026-09-17), matching the schema
end to end — the full `books.json` produced by an actual run will hold 60 of these:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_gbp": 51.77,
  "price_text": "£51.77",
  "in_stock": true,
  "stock_count": 22,
  "availability_text": "In stock (22 available)",
  "rating": 3,
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition.",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-09-17T11:02:00Z"
}
```

A representative `run-report.json` from a clean run (paste your own actual one here after you
run it — durations and timestamps will differ):

```json
{
  "start_time": "2026-09-17T11:00:00Z",
  "duration_seconds": 38.4,
  "pages_fetched": 63,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```
`pages_fetched` is 3 catalogue pages + 60 book pages = 63; at a ≥0.5s delay between requests
that's roughly 30+ seconds minimum, which matches the duration above.

## Known limitation

Ratings and availability counts on this sandbox are randomly assigned by the site and carry
no real meaning (the site says so directly) — they're collected and normalized faithfully,
but shouldn't be read as real signals about the books.

## Ethics note

- Prefer an official API over scraping whenever one exists; this site has none, and exists
  specifically so scraping is the intended way to get its data.
- Never bypass a login, a paywall, or a block — a `403` or a login wall means "no," not "try
  harder."
- Collect only what the task actually needs — three catalogue pages here, not all 1000 books.
- Identify the scraper honestly (a real user-agent), go slowly, and check `robots.txt` before
  writing a single line of request code, every time, on every new site.