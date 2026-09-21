"""
Stage 4 checkpoint: normalize every raw record, validate it against the
schema, and store it. Good records go to output/books.json; anything
that fails validation goes to output/errors.json with a reason.

Running this twice must produce the same 60 records in books.json, not
120 - that's idempotency, and it's what makes re-running a failed job safe.

Run:
    python -m src.main
"""
import json
import pathlib
from datetime import datetime, timezone

from pydantic import ValidationError

from src.fetcher import fetch
from src.parser import find_book_links, find_next_page, extract_book_record
from src.schema import raw_to_record

CATALOGUE_START = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"


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


def extract_validate_all(book_urls: list[str]) -> tuple[list[dict], list[dict]]:
    valid, errors = [], []
    for product_url in book_urls:
        detail_html = fetch(product_url)
        raw = extract_book_record(detail_html, product_url, CATALOGUE_START, now_iso())
        try:
            record = raw_to_record(raw)
            valid.append(json.loads(record.model_dump_json()))
        except (ValidationError, ValueError) as exc:
            errors.append({"url": product_url, "reason": str(exc)})
    return valid, errors


def deduplicate_by_url(records: list[dict]) -> list[dict]:
    """A record's canonical URL is its identity - keeps reruns idempotent."""
    seen = {}
    for record in records:
        seen[record["product_url"]] = record
    return list(seen.values())


if __name__ == "__main__":
    book_urls = discover_book_urls()
    valid_records, error_records = extract_validate_all(book_urls)
    valid_records = deduplicate_by_url(valid_records)

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "books.json").write_text(json.dumps(valid_records, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "errors.json").write_text(json.dumps(error_records, indent=2), encoding="utf-8")
    print(f"valid={len(valid_records)} invalid={len(error_records)}")
