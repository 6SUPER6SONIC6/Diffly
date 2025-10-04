from scrapers.xbox.xbox.xbox_games_scraper import XboxGamesScraper


class ScraperFactory:
    """Factory that creates scraper instances."""
    _registry = {
        ("xbox", "games"): XboxGamesScraper,
    }

    @classmethod
    def get(cls, platform, scrape_type):
        key = (platform.lower(), scrape_type.lower())
        scraper_class = cls._registry.get(key)
        if not scraper_class:
            raise ValueError(f"No scraper found for {platform} {scrape_type}")
        return scraper_class()