"""
Polite fetching: a saved-copy cache, an honest user-agent, a timeout,
a status check, and a minimum delay between real requests to the site.

Cached pages never leave the computer, so they need no delay and don't
count toward the politeness rules below.
"""
import time
import pathlib
import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/zaidzia46/FlyRank-AI-Internship)"
TIMEOUT_SECONDS = 10
MIN_DELAY_SECONDS = 0.5
CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / "cache"

# Simple counters the run report reads at the end of a run.
stats = {"fetches": 0, "cache_hits": 0}


def reset_stats():
    stats["fetches"] = 0
    stats["cache_hits"] = 0


class FetchError(Exception):
    """Raised when a page could not be fetched with a 200 status."""

    def __init__(self, url, status_code=None, reason=""):
        self.url = url
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"{reason} ({url}, status={status_code})")


_last_request_time = 0.0


def _cache_path_for(url: str) -> pathlib.Path:
    """Turn a URL into a flat, readable cache filename."""
    name = url.split("://", 1)[-1].replace("/", "_")
    if not name.endswith(".html"):
        name += ".html"
    return CACHE_DIR / name


def _wait_for_politeness():
    """Block until at least MIN_DELAY_SECONDS have passed since the last real request."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < MIN_DELAY_SECONDS:
        time.sleep(MIN_DELAY_SECONDS - elapsed)


def fetch(url: str, use_cache: bool = True) -> str:
    """
    Return the HTML at `url`.

    Reads cache/ first if a saved copy exists. Otherwise makes one real,
    polite request - identifying user-agent, a timeout, a status check,
    a minimum delay since the previous real request - and saves the
    result before returning it.

    Raises FetchError for anything other than HTTP 200.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = _cache_path_for(url)

    if use_cache and cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        stats["cache_hits"] += 1
        print(f"CACHE HIT {url} ({len(html)} bytes)")
        return html

    global _last_request_time
    _wait_for_politeness()

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout as exc:
        _last_request_time = time.monotonic()
        raise FetchError(url, status_code=None, reason="timeout") from exc
    except requests.exceptions.RequestException as exc:
        _last_request_time = time.monotonic()
        raise FetchError(url, status_code=None, reason=str(exc)) from exc

    _last_request_time = time.monotonic()

    if response.status_code != 200:
        raise FetchError(url, status_code=response.status_code, reason="non-200 status")

    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    stats["fetches"] += 1
    print(f"FETCH {url} ({len(html)} bytes)")
    return html


def fetch_with_retry(url: str, use_cache: bool = True, max_retries: int = 1) -> str:
    """
    Same as fetch(), but on a timeout or a 5xx server error, waits a
    moment and tries once more.

    Never retries a 404 (the page does not exist) or a 403 (the site
    said no) - asking again won't fix either of those, it would just
    be rude.
    """
    attempts = 0
    while True:
        try:
            return fetch(url, use_cache=use_cache)
        except FetchError as exc:
            attempts += 1
            is_retryable = exc.status_code is None or exc.status_code >= 500
            if not is_retryable or attempts > max_retries:
                raise
            wait = 2 * attempts
            print(f"RETRY {url} in {wait}s (attempt {attempts}) - {exc.reason}")
            time.sleep(wait)
