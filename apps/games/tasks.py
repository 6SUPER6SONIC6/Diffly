from celery import shared_task

from scrapers.factory import ScraperFactory


@shared_task
def scrape_xbox_games_task():
    scraper = ScraperFactory.get('xbox', 'games')
    scraper.run(max_pages=2)
