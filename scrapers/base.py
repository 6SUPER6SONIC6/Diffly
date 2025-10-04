from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Abstract base class for scrapers."""

    @abstractmethod
    def run(self, **kwargs):
        """Abstract method to run the scraper."""
        pass