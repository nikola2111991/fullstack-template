"""
Async Web Scraper — Rate limited, retry, concurrent, CSV/JSON export
Usage:
    scraper = MyScraper()
    results = await scraper.run(urls, max_concurrent=3)
    BaseScraper.export_csv(results, "output.csv")
"""
from __future__ import annotations
import asyncio, csv, json, logging, random, time
from dataclasses import dataclass, asdict, fields
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ScrapedItem:
    name: str
    url: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    rating: float = 0.0
    review_count: int = 0
    notes: str = ""

    def is_valid(self) -> bool:
        return bool(self.name and (self.phone or self.email or self.url))


class RateLimiter:
    def __init__(self, min_delay=1.5, max_delay=4.0):
        self.min_delay, self.max_delay, self.last = min_delay, max_delay, 0.0
    async def wait(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        elapsed = time.time() - self.last
        if elapsed < delay: await asyncio.sleep(delay - elapsed)
        self.last = time.time()


class BaseScraper:
    def __init__(self, max_retries=3, timeout=15.0, min_delay=1.5, max_delay=4.0):
        self.max_retries = max_retries
        self.limiter = RateLimiter(min_delay, max_delay)
        self.client = httpx.AsyncClient(timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }, follow_redirects=True)
        self.stats = {"total": 0, "success": 0, "failed": 0}

    async def fetch(self, url: str) -> str:
        await self.limiter.wait()
        for attempt in range(self.max_retries):
            try:
                r = await self.client.get(url)
                r.raise_for_status()
                self.stats["success"] += 1
                return r.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: await asyncio.sleep(10 * (attempt + 1))
                elif e.response.status_code == 404: return ""
            except (httpx.TimeoutException, httpx.ConnectError):
                await asyncio.sleep(2 ** attempt)
        self.stats["failed"] += 1
        return ""

    async def scrape_page(self, url: str) -> list[ScrapedItem]:
        raise NotImplementedError

    async def run(self, urls: list[str], max_concurrent=3) -> list[ScrapedItem]:
        self.stats["total"] = len(urls)
        sem = asyncio.Semaphore(max_concurrent)
        async def bounded(url):
            async with sem:
                try: return await self.scrape_page(url)
                except Exception as e:
                    logger.error(f"Failed {url}: {e}")
                    return []
        results = await asyncio.gather(*[bounded(u) for u in urls])
        items = [i for batch in results for i in batch if i.is_valid()]
        logger.info(f"Done: {self.stats} | Valid: {len(items)}")
        return items

    @staticmethod
    def export_csv(items: list[ScrapedItem], filepath: str | Path):
        if not items: return
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[x.name for x in fields(items[0])])
            w.writeheader()
            for i in items: w.writerow(asdict(i))

    @staticmethod
    def export_json(items: list[ScrapedItem], filepath: str | Path):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(i) for i in items], f, ensure_ascii=False, indent=2)

    async def close(self): await self.client.aclose()
