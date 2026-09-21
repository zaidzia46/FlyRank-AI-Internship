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
- is saved to `cache/` — while developing, a page is asked for once; every run after that
  reads the saved copy instead

## Try it

```bash
pip install -r requirements.txt
python -m src.main   # first run: FETCH ... and creates cache/
python -m src.main   # second run: CACHE HIT ... (no new request sent)
```

## Status

Stage 1 commit — polite fetch-with-cache is working for a single page. Discovery, extraction,
validation, and the run report come in later commits.
