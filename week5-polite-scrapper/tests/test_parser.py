"""
Unit tests that run against saved fixtures, never against the live site.
Covers: price normalization, relative->absolute URLs, missing description,
duplicate URLs, and one malformed fixture.

Run:
    python -m pytest tests/ -v
"""
import pathlib
import pytest

from src.parser import find_book_links, find_next_page, extract_book_record
from src.schema import normalize_price, normalize_availability, normalize_rating, raw_to_record

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"


def test_price_normalization():
    assert normalize_price("£51.77") == 51.77
    assert normalize_price("£5.00") == 5.00


def test_availability_normalization():
    in_stock, count = normalize_availability("In stock (22 available)")
    assert in_stock is True
    assert count == 22

    in_stock2, count2 = normalize_availability("Out of stock")
    assert in_stock2 is False
    assert count2 is None


def test_relative_to_absolute_url():
    catalogue_html = (FIXTURES / "catalogue_page.html").read_text()
    links = find_book_links(catalogue_html, PAGE_URL)
    assert links[0] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert all(link.startswith("https://") for link in links)


def test_missing_description_is_null_not_invented():
    detail_html = (FIXTURES / "book_no_description.html").read_text()
    raw = extract_book_record(detail_html, "https://example.com/book", PAGE_URL, "2026-09-17T00:00:00Z")
    assert raw["description"] is None
    record = raw_to_record(raw)
    assert record.description is None


def test_duplicate_urls_collapse_to_one():
    urls = [
        "https://books.toscrape.com/catalogue/a_1/index.html",
        "https://books.toscrape.com/catalogue/b_2/index.html",
        "https://books.toscrape.com/catalogue/a_1/index.html",  # duplicate
    ]
    unique = list(dict.fromkeys(urls))
    assert len(unique) == 2


def test_malformed_fixture_missing_price_raises_clear_error():
    malformed_html = """
    <html><body>
    <div class="col-sm-6 product_main">
      <h1>Broken Book</h1>
      <p class="instock availability">In stock (1 available)</p>
      <p class="star-rating One"></p>
    </div>
    </body></html>
    """
    with pytest.raises(AttributeError):
        # no p.price_color on the page -> selector returns None -> .get_text() fails
        extract_book_record(malformed_html, "https://example.com/broken", PAGE_URL, "2026-09-17T00:00:00Z")


def test_rating_word_to_number():
    assert normalize_rating("Three") == 3
    assert normalize_rating("One") == 1
    assert normalize_rating(None) is None


def test_next_page_link_resolves_absolute():
    catalogue_html = (FIXTURES / "catalogue_page.html").read_text()
    next_url = find_next_page(catalogue_html, PAGE_URL)
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"
