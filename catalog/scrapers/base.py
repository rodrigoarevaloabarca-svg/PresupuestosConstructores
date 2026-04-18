import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'es-CL,es;q=0.9',
    'Accept': 'application/json, text/html, */*',
}


class BaseRetailerScraper(ABC):
    retailer_slug: str = ''
    rate_limit_seconds: float = 2.0

    def __init__(self):
        self.headers = BROWSER_HEADERS.copy()

    @abstractmethod
    async def search(self, q: str) -> list[dict]:
        """Busca productos por query. Retorna lista de dicts con keys:
        name, price_clp, url, sku (opcional), category (opcional).
        """

    async def search_many(self, queries: list[str]) -> list[dict]:
        results = []
        for q in queries:
            try:
                items = await self.search(q)
                results.extend(items)
            except Exception as exc:
                logger.error('[%s] Error buscando "%s": %s', self.retailer_slug, q, exc)
            await asyncio.sleep(self.rate_limit_seconds)
        return results

    def upsert_products(self, products: list[dict]) -> int:
        """Guarda o actualiza los productos en RetailerProduct. Retorna cantidad upserted."""
        from catalog.models import RetailerProduct
        from django.utils import timezone

        count = 0
        for p in products:
            sku = p.get('sku') or None
            defaults = {
                'name': p['name'][:500],
                'price_clp': int(p['price_clp']),
                'url': p['url'][:1000],
                'category': (p.get('category') or '')[:200] or None,
                'is_active': True,
            }
            if sku:
                obj, _ = RetailerProduct.objects.update_or_create(
                    retailer=self.retailer_slug, sku=sku, defaults=defaults,
                )
            else:
                obj, _ = RetailerProduct.objects.update_or_create(
                    retailer=self.retailer_slug, name=p['name'][:500],
                    defaults=defaults,
                )
            count += 1
        return count
