"""
Turns saved catalogue and book-detail HTML into raw fields.
Nothing here normalizes or validates - that happens in schema.py.
"""
from urllib.parse import urljoin
from bs4 import BeautifulSoup

RATING_WORDS = {"One", "Two", "Three", "Four", "Five"}


def find_book_links(catalogue_html: str, page_url: str) -> list[str]:
    """Return the absolute URL of every book on one catalogue page."""
    soup = BeautifulSoup(catalogue_html, "html.parser")
    links = []
    for article in soup.select("article.product_pod"):
        href = article.select_one("h3 a")["href"]
        # relative URLs are turned absolute with urljoin, never by gluing strings
        links.append(urljoin(page_url, href))
    return links


def find_next_page(catalogue_html: str, page_url: str) -> str | None:
    """Return the absolute URL of the catalogue's own 'next' link, or None on the last page."""
    soup = BeautifulSoup(catalogue_html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link is None:
        return None
    return urljoin(page_url, next_link["href"])
