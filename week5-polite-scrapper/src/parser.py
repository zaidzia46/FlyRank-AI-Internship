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


def extract_book_record(detail_html: str, product_url: str, source_page: str, fetched_at: str) -> dict:
    """
    Pull the eight raw fields from one book's detail page.
    Selectors are aimed at the product area (div.product_main), not the
    whole document, so a second price elsewhere on the page can't fool us.
    """
    soup = BeautifulSoup(detail_html, "html.parser")
    main = soup.select_one("div.product_main")

    title = main.select_one("h1").get_text(strip=True)
    price_text = main.select_one("p.price_color").get_text(strip=True)
    availability_text = " ".join(main.select_one("p.availability").get_text().split())

    rating_tag = main.select_one("p.star-rating")
    rating_text = next((c for c in rating_tag.get("class", []) if c in RATING_WORDS), None)

    # Some books have no description section at all - store null, never invent text.
    description_heading = soup.select_one("#product_description")
    if description_heading is not None:
        description_p = description_heading.find_next_sibling("p")
        description = description_p.get_text(strip=True) if description_p else None
    else:
        description = None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
