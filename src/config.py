"""Central configuration for the polite scraper."""

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

# Identifies this scraper to the site (polite scraping practice).
USER_AGENT = "FlyRankInternProject/1.0 (educational; contact: qiwei li)"

# Minimum seconds between HTTP requests.
REQUEST_DELAY = 1.0

# Number of catalogue pages to scrape (20 books per page).
PAGE_COUNT = 3
EXPECTED_BOOKS = PAGE_COUNT * 20

# Network / retry behavior.
REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 1          # one retry after the initial attempt
RETRY_BACKOFF = 2.0      # seconds to wait before the single retry
