import asyncio
import feedparser
import httpx
import logging
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
from time import mktime

logger = logging.getLogger("crawler-service")

class AbstractNewsScraper(ABC):
    @abstractmethod
    async def scrape(self) -> List[Dict]:
        """
        Scrape news articles and return a list of dictionaries.
        """
        pass

class RSSScraper(AbstractNewsScraper):
    def __init__(self, source_name: str, rss_url: str):
        self.source_name = source_name
        self.rss_url = rss_url
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/90.0.4430.93 Safari/537.36"
            )
        }

    async def scrape(self) -> List[Dict]:
        logger.info(f"Scraping {self.source_name} RSS feed...")
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=self.headers) as client:
                response = await client.get(self.rss_url)
                response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            articles = []
            for entry in feed.entries:
                published_dt = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_dt = datetime.fromtimestamp(mktime(entry.published_parsed))
                
                articles.append({
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link", ""),
                    "content": entry.get("summary", "") or entry.get("description", ""),
                    "source": self.source_name,
                    "published_at": published_dt
                })
            return articles
        except Exception as e:
            logger.error(f"Error scraping {self.source_name}: {e}")
            return []

# Factory for creating scrapers
def get_scrapers() -> List[AbstractNewsScraper]:
    return [
        RSSScraper("FDA Press Releases", "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml"),
        RSSScraper("NIH News", "https://www.nih.gov/news-events/feed.xml"),
        RSSScraper("ScienceDaily (Medicine)", "https://www.sciencedaily.com/rss/health_medicine.xml"),
        RSSScraper("Medical Xpress", "https://medicalxpress.com/rss-feed/"),
        RSSScraper("Drug Discovery News", "https://www.drugdiscoverynews.com/rss")
    ]
