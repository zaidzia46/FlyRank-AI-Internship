"""
Stage 2 checkpoint: follow the catalogue's own "next" link for 3 pages,
collect the link to every book, and de-duplicate.

Run:
    python -m src.main
"""
from src.fetcher import fetch
from src.parser import find_book_links, find_next_page

CATALOGUE_START = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


def discover_book_urls() -> list[str]:
    urls = []
    page_url = CATALOGUE_START
    pages_visited = 0

    while page_url and pages_visited < MAX_CATALOGUE_PAGES:
        html = fetch(page_url)
        urls.extend(find_book_links(html, page_url))
        page_url = find_next_page(html, page_url)  # let the site tell us what's next
        pages_visited += 1

    unique_urls = list(dict.fromkeys(urls))  # de-duplicate, keep order
    print(f"catalogue_pages={pages_visited} discovered={len(urls)} unique_urls={len(unique_urls)}")
    return unique_urls


if __name__ == "__main__":
    discover_book_urls()
