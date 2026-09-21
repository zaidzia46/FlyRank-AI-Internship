"""
The polite scraper - entry point.

Fetches the first 3 catalogue pages of Books to Scrape, visits every
book, normalizes and validates every record, survives a broken page,
and ends every run with a short honest report.

Run:
    python -m src.main
    python -m src.main --inject-broken-url    # Stage 5 checkpoint: proves
                                               # one bad page can't kill the run
"""
import json
import pathlib
import argparse
from datetime import datetime, timezone

from pydantic import ValidationError

from src import fetcher
from src.fetcher import fetch_with_retry, FetchError
from src.parser import find_book_links, find_next_page, extract_book_record
from src.schema import raw_to_record

CATALOGUE_START = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
FAKE_BOOK_URL = "https://books.toscrape.com/catalogue/this-book-does-not-exist_0/index.html"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_book_urls() -> tuple[list[str], int]:
    """
    Walk the catalogue's own 'next' links for up to MAX_CATALOGUE_PAGES,
    collecting every book URL. Returns (unique_urls, pages_visited).
    """
    urls = []
    page_url = CATALOGUE_START
    pages_visited = 0

    while page_url and pages_visited < MAX_CATALOGUE_PAGES:
        html = fetch_with_retry(page_url)
        urls.extend(find_book_links(html, page_url))
        page_url = find_next_page(html, page_url)
        pages_visited += 1

    unique_urls = list(dict.fromkeys(urls))  # de-duplicate, keep order
    print(f"catalogue_pages={pages_visited} discovered={len(urls)} unique_urls={len(unique_urls)}")
    return unique_urls, pages_visited


def extract_and_validate(book_urls: list[str]) -> tuple[list[dict], list[dict]]:
    """
    Visit every book URL, one at a time. A page that fails to fetch, or
    a record that fails validation, is logged to error_records and
    skipped - it never takes the whole run down.
    """
    valid_records = []
    error_records = []

    for product_url in book_urls:
        try:
            detail_html = fetch_with_retry(product_url)
        except FetchError as exc:
            error_records.append({"url": product_url, "reason": f"fetch failed: {exc.reason}"})
            print(f"SKIP {product_url}: fetch failed ({exc.reason})")
            continue

        try:
            raw = extract_book_record(
                detail_html,
                product_url=product_url,
                source_page=CATALOGUE_START,
                fetched_at=now_iso(),
            )
            record = raw_to_record(raw)
            valid_records.append(json.loads(record.model_dump_json()))
        except (ValidationError, ValueError, AttributeError) as exc:
            error_records.append({"url": product_url, "reason": f"validation failed: {exc}"})
            print(f"SKIP {product_url}: validation failed ({exc})")

    return valid_records, error_records


def deduplicate_by_url(records: list[dict]) -> list[dict]:
    """A record's canonical URL is its identity - the same book counts once, keeping reruns idempotent."""
    seen = {}
    for record in records:
        seen[record["product_url"]] = record
    return list(seen.values())


def main():
    parser = argparse.ArgumentParser(description="The polite scraper - Books to Scrape")
    parser.add_argument(
        "--inject-broken-url",
        action="store_true",
        help="Add one made-up book URL to prove a broken page can't take the run down.",
    )
    args = parser.parse_args()

    fetcher.reset_stats()
    start_time = datetime.now(timezone.utc)

    book_urls, _pages_visited = discover_book_urls()
    if args.inject_broken_url:
        book_urls.append(FAKE_BOOK_URL)
        print(f"INJECTED broken URL for testing: {FAKE_BOOK_URL}")

    valid_records, error_records = extract_and_validate(book_urls)
    valid_records = deduplicate_by_url(valid_records)
    failed_pages = sum(1 for e in error_records if e["reason"].startswith("fetch failed"))
    invalid_records = sum(1 for e in error_records if e["reason"].startswith("validation failed"))

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "books.json").write_text(json.dumps(valid_records, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "errors.json").write_text(json.dumps(error_records, indent=2), encoding="utf-8")

    end_time = datetime.now(timezone.utc)
    run_report = {
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2),
        "pages_fetched": fetcher.stats["fetches"],
        "cache_hits": fetcher.stats["cache_hits"],
        "valid_records": len(valid_records),
        "invalid_records": invalid_records,
        "failed_pages": failed_pages,
    }
    (OUTPUT_DIR / "run-report.json").write_text(json.dumps(run_report, indent=2), encoding="utf-8")

    print(json.dumps(run_report, indent=2))


if __name__ == "__main__":
    main()
