"""
Stage 3 checkpoint: visit every discovered book page and pull out the
eight raw fields. Nothing is normalized or validated yet - that's Stage 4.

Run:
    python -m src.main
"""
import json
from datetime import datetime, timezone

from src.fetcher import fetch
from src.parser import find_book_links, find_next_page, extract_book_record

CATALOGUE_START = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_book_urls() -> list[str]:
    urls = []
    page_url = CATALOGUE_START
    pages_visited = 0
    while page_url and pages_visited < MAX_CATALOGUE_PAGES:
        html = fetch(page_url)
        urls.extend(find_book_links(html, page_url))
        page_url = find_next_page(html, page_url)
        pages_visited += 1
    return list(dict.fromkeys(urls))


def extract_all(book_urls: list[str]) -> list[dict]:
    records = []
    for product_url in book_urls:
        detail_html = fetch(product_url)
        raw = extract_book_record(detail_html, product_url, CATALOGUE_START, now_iso())
        records.append(raw)
    return records


if __name__ == "__main__":
    book_urls = discover_book_urls()
    raw_records = extract_all(book_urls)
    print(json.dumps(raw_records[0], indent=2))
    print(f"detail_pages={len(raw_records)}")
