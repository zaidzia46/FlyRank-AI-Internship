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

## Status

Stage 5 commit — the run survives a broken page and reports honest numbers at the end.
Verified end to end (discovery → extraction → normalization → validation → idempotent
storage → failure survival → report) against a local test server. Publishing polish — final
README, ethics note, and parser tests — comes in the next commit.
