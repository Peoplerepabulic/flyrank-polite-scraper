"""Validate + collect: raw dicts -> validated Book models.

Invalid records are logged and skipped; the pipeline never crashes.
"""

import logging

from pydantic import ValidationError

from .schemas import Book

logger = logging.getLogger(__name__)


def collect_books(raw_books: list[dict]) -> list[Book]:
    """Validate each raw dict; return only the ones that pass."""
    books: list[Book] = []
    for raw in raw_books:
        try:
            books.append(Book(**raw))
        except (ValidationError, TypeError) as exc:
            logger.warning("skipping invalid record %r: %s", raw, exc)
    logger.info("validated %d/%d records", len(books), len(raw_books))
    return books
