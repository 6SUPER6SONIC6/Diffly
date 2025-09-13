import os
import sys
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scrapers.base import BaseScraper
from scrapers.xbox.xbox.spiders.game import GameSpider


class XboxGamesScraper(BaseScraper):
    """Scraper wrapper for Xbox games using GameSider"""

    def run(self, max_pages=3, **kwargs):
        xbox_scraper_path = str(Path(__file__).parent.parent.absolute())
        if xbox_scraper_path not in sys.path:
            sys.path.append(xbox_scraper_path)
        os.environ['SCRAPY_SETTINGS_MODULE'] = 'xbox.settings'

        process = CrawlerProcess(get_project_settings())
        process.crawl(GameSpider, max_pages=max_pages)
        process.start()