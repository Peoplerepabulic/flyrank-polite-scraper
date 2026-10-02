"""Polite HTTP fetching: robots.txt check, rate limiting, retries."""

import logging
import time
from urllib.parse import urljoin, urlparse

import requests

from . import config

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": config.USER_AGENT})

_last_request_time = 0.0


def _polite_wait() -> None:
    """Sleep so that at least REQUEST_DELAY seconds pass between requests."""
    global _last_request_time
    now = time.monotonic()
    wait = config.REQUEST_DELAY - (now - _last_request_time)
    if wait > 0:
        logger.debug("rate limiting: sleeping %.2fs", wait)
        time.sleep(wait)
    _last_request_time = time.monotonic()


def _disallows(url: str, body: str) -> bool:
    """Very small robots.txt evaluator: True if any 'Disallow' blocks `url`."""
    path = urlparse(url).path or "/"
    for line in body.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.lower().startswith("disallow:"):
            rule = line.split(":", 1)[1].strip()
            if rule and path.startswith(rule):
                return True
    return False


def check_robots_txt() -> bool:
    """Fetch robots.txt FIRST; return True only if scraping may proceed.

    A 404 (no robots.txt) means nothing is disallowed per the robots
    exclusion protocol. Any explicit disallow of the catalogue pages
    makes this return False so the run aborts before any scraping.
    """
    robots_url = urljoin(config.BASE_URL, "/robots.txt")
    logger.info("checking %s", robots_url)
    try:
        resp = SESSION.get(robots_url, timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("could not fetch robots.txt (%s); continuing anyway", exc)
        return True

    logger.info("robots.txt -> HTTP %s", resp.status_code)
    if resp.status_code == 404:
        logger.info(
            "robots.txt not found (404): no paths disallowed; "
            "books.toscrape.com is a dedicated scraping sandbox"
        )
        return True
    if not resp.ok:
        logger.warning("robots.txt returned %s; continuing cautiously", resp.status_code)
        return True

    logger.info("robots.txt contents:\n%s", resp.text.strip())
    for page in range(1, config.PAGE_COUNT + 1):
        url = config.CATALOGUE_URL.format(page)
        if _disallows(url, resp.text):
            logger.error("robots.txt disallows %s; aborting", url)
            return False
    logger.info("robots.txt allows the catalogue pages; proceeding")
    return True


def fetch(url: str) -> str | None:
    """GET `url` with rate limiting; retry once on failure, else None."""
    attempts = 1 + config.MAX_RETRIES
    for attempt in range(1, attempts + 1):
        _polite_wait()
        logger.info("fetching %s (attempt %d/%d)", url, attempt, attempts)
        try:
            resp = SESSION.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            logger.info("fetched %s: HTTP %s, %d bytes", url, resp.status_code, len(resp.text))
            return resp.text
        except requests.RequestException as exc:
            logger.warning("fetch failed for %s: %s", url, exc)
            if attempt < attempts:
                logger.info("retrying in %.1fs", config.RETRY_BACKOFF)
                time.sleep(config.RETRY_BACKOFF)
    logger.error("giving up on %s after %d attempts; skipping page", url, attempts)
    return None
