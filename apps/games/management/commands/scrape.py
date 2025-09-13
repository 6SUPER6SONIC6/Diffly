from django.core.management import BaseCommand, CommandError

from scrapers.factory import ScraperFactory


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('platform', choices=['xbox'])
        parser.add_argument('type', choices=['games'])
        parser.add_argument(
            '-p',
            '--pages',
            type=int,
            default=3,
            help='Number of pages to scrape (default: 3)',
        )

    def handle(self, *args, **options):
        platform = options['platform']
        scrape_type = options['type']
        max_pages = options['pages']

        try:
            scraper = ScraperFactory.get(platform, scrape_type)
        except ValueError as e:
            raise CommandError(e)

        scraper.run(max_pages=max_pages)

        self.stdout.write(self.style.SUCCESS(f'Scraping {platform}/{scrape_type} for {max_pages} pages complete.'))