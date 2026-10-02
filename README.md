# flyrank-polite-scraper

A polite, schema-validated web scraper for [books.toscrape.com](https://books.toscrape.com/)
(a sandbox site made specifically for scraping practice). It scrapes the first
3 catalogue pages (60 books) and writes clean, validated JSON to
`data/books.json`.

## Prerequisites

- Python 3.10+
- A virtual environment is recommended

## Setup & run (5 minutes)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

What gets produced:

- `data/books.json` — a JSON array with exactly 60 validated book records.

Each record looks like this:

```json
{
  "title": "A Light in the Attic",
  "price": 51.77,
  "rating": 3,
  "in_stock": true,
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
}
```

| field       | type   | description                                     |
| ----------- | ------ | ----------------------------------------------- |
| title       | string | book title, whitespace stripped                 |
| price       | float  | price in GBP (parsed from e.g. `"£51.77"`)      |
| rating      | int    | 1–5 (parsed from e.g. `"star-rating Three"`)    |
| in_stock    | bool   | `true` when the listing says "In stock"         |
| product_url | string | absolute URL of the book's product page         |

## Politeness (this is the point of the exercise)

- **robots.txt is checked first.** `src/fetcher.py` fetches
  `https://books.toscrape.com/robots.txt` before any scraping and only
  proceeds if catalogue pages are not disallowed. At the time of writing the
  site returns **404 (no robots.txt exists)**, which per the robots exclusion
  protocol means *no paths are disallowed* — and the site itself exists as a
  scraping sandbox. This finding is logged at runtime.
- **Identifies itself.** Every request carries a polite User-Agent:
  `FlyRankInternProject/1.0 (educational; contact: qiwei li)`.
- **Rate-limited.** At least 1 second between requests (`REQUEST_DELAY = 1.0`
  in `src/config.py`); each fetch is logged.

## Robustness

- HTTP errors / timeouts are logged, retried once with backoff, then the page
  is skipped and the scraper continues.
- A malformed book card is skipped with a warning; the scraper never crashes
  on a bad card.
- Every record is validated with a pydantic v2 `Book` model (`src/schemas.py`);
  invalid records are logged and dropped.

## Layout

```
src/
  config.py     base URL, user agent, delays, page count
  fetcher.py    robots.txt check + polite fetching with retries
  parser.py     messy HTML -> raw dicts
  schemas.py    pydantic Book model
  pipeline.py   validate + collect (skip-invalid logic)
  main.py       CLI entry: python -m src.main
data/
  books.json    the 60 scraped books (deliverable)
```
