"""Parse messy books.toscrape.com HTML into raw book dicts."""

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def _parse_price(text: str) -> float:
    """'£51.77' -> 51.77 (strips currency symbols, keeps digits/dot)."""
    cleaned = re.sub(r"[^0-9.]", "", text)
    if not cleaned:
        raise ValueError(f"no numeric price in {text!r}")
    return float(cleaned)


def _parse_rating(classes: list[str]) -> int:
    """['star-rating', 'Three'] -> 3."""
    for cls in classes:
        if cls in RATING_WORDS:
            return RATING_WORDS[cls]
    raise ValueError(f"unknown rating classes {classes!r}")


def parse_book_card(card, page_url: str) -> dict:
    """Parse one <article class='product_pod'> into a raw dict.

    `page_url` is the catalogue page URL; relative hrefs are resolved
    against it so product URLs point at the real /catalogue/ paths.
    Raises ValueError for any malformed card; the caller decides to skip.
    """
    title_tag = card.select_one("h3 a")
    if title_tag is None or not title_tag.get("title"):
        raise ValueError("missing title link")
    title = title_tag["title"].strip()
    if not title:
        raise ValueError("empty title")

    href = title_tag.get("href", "")
    if not href:
        raise ValueError(f"missing product link for {title!r}")
    product_url = urljoin(page_url, href)

    price_tag = card.select_one("p.price_color")
    if price_tag is None:
        raise ValueError(f"missing price for {title!r}")
    price = _parse_price(price_tag.get_text())

    rating_tag = card.select_one("p.star-rating")
    if rating_tag is None:
        raise ValueError(f"missing rating for {title!r}")
    rating = _parse_rating(rating_tag.get("class", []))

    avail_tag = card.select_one("p.instock.availability")
    in_stock = bool(avail_tag) and "in stock" in avail_tag.get_text().lower()

    return {
        "title": title,
        "price": price,
        "rating": rating,
        "in_stock": in_stock,
        "product_url": product_url,
    }


def parse_page(html: str, page_url: str) -> list[dict]:
    """Parse a catalogue page; malformed cards are skipped with a warning."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article.product_pod")
    raw_books: list[dict] = []
    for card in cards:
        try:
            raw_books.append(parse_book_card(card, page_url))
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning("skipping malformed book card: %s", exc)
    logger.info("parsed %d/%d book cards", len(raw_books), len(cards))
    return raw_books
