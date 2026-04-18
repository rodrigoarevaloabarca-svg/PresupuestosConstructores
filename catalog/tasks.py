import asyncio
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

QUERIES = [
    'cemento', 'cañería', 'cable eléctrico', 'pintura',
    'llave paso', 'tomacorriente', 'teja', 'perno', 'silicon',
]


@shared_task(bind=True, max_retries=2)
def scrape_all_retailers(self):
    from catalog.scrapers.sodimac import SodimacScraper
    from catalog.scrapers.easy import EasyScraper
    from catalog.scrapers.imperial import ImperialScraper
    from catalog.models import RetailerProduct
    from django.utils import timezone
    from datetime import timedelta

    scrapers = [SodimacScraper(), EasyScraper(), ImperialScraper()]
    total = 0

    async def run():
        nonlocal total
        tasks = [s.search_many(QUERIES) for s in scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for scraper, result in zip(scrapers, results):
            if isinstance(result, Exception):
                logger.error('[%s] scrape failed: %s', scraper.retailer_slug, result)
                continue
            count = scraper.upsert_products(result)
            total += count
            logger.info('[%s] %d upserted', scraper.retailer_slug, count)

    try:
        asyncio.run(run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * 10)

    if total < 50:
        logger.error('Scraper returned only %d products — possible breakage', total)

    # Desactivar productos con más de 60 días sin actualizar
    cutoff = timezone.now() - timedelta(days=60)
    RetailerProduct.objects.filter(last_scraped__lt=cutoff).update(is_active=False)

    return f'{total} products upserted'
