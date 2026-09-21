"""
Stage 1 checkpoint: fetch catalogue page 1 politely, then prove that a
second run reads from the cache instead of asking the site again.

Run this twice:
    python -m src.main
    python -m src.main
The first run prints FETCH and creates cache/..., the second prints CACHE HIT.
"""
from src.fetcher import fetch

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"

if __name__ == "__main__":
    fetch(CATALOGUE_PAGE_1)
