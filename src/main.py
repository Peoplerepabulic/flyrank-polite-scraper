"""CLI entry: python -m src.main

Scrapes the first N catalogue pages politely and writes data/books.json.
"""

import json
import logging
import sys
from pathlib import Path

from . import config, fetcher, parser, pipeline

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "books.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main() -> int:
    logger = logging.getLogger("main")

    if not fetcher.check_robots_txt():
        logger.error("aborting: robots.txt disallows the catalogue pages")
        return 1

    raw_books: list[dict] = []
    for page in range(1, config.PAGE_COUNT + 1):
        url = config.CATALOGUE_URL.format(page)
        html = fetcher.fetch(url)
        if html is None:
            logger.warning("page %d skipped (fetch failed); continuing", page)
            continue
        raw_books.extend(parser.parse_page(html, url))

    books = pipeline.collect_books(raw_books)
    logger.info("collected %d valid books (expected %d)", len(books), config.EXPECTED_BOOKS)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [b.model_dump(mode="json") for b in books]
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    logger.info("wrote %s (%d records)", OUTPUT_PATH, len(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
