# Scrapy settings for xbox project
import os
import sys

import django

sys.path.append(os.path.abspath('../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'Diffly.settings'
django.setup()


BOT_NAME = "xbox"

SPIDER_MODULES = ["xbox.spiders"]
NEWSPIDER_MODULE = "xbox.spiders"

ITEM_PIPELINES = {
    "xbox.pipelines.DjangoModelPipeline": 300,
}

ADDONS = {}

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Request pacing
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True

# Retries and timeout
RETRY_ENABLED = True
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 20
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 520, 521, 522, 524]

# Throttling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1
AUTOTHROTTLE_DEBUG = True

# Headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Referer": "https://www.xbox.com/",
    "Sec-Ch-Ua": 'Chromium";v="139", "Not;A=Brand";v="99',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "x-ms-api-version": "1.1"
}

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
