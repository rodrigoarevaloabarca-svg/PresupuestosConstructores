import asyncio
import logging

from django.core.management.base import BaseCommand

from catalog.scrapers.easy import EasyScraper
from catalog.scrapers.imperial import ImperialScraper
from catalog.scrapers.sodimac import SodimacScraper

logger = logging.getLogger(__name__)

QUERIES = [
    'cemento', 'cañería', 'cable eléctrico', 'pintura',
    'llave paso', 'tomacorriente', 'teja', 'perno', 'silicon',
]

SCRAPERS = {
    'sodimac': SodimacScraper,
    'easy': EasyScraper,
    'imperial': ImperialScraper,
}


class Command(BaseCommand):
    help = 'Scrape productos de ferreterías (sodimac, easy, imperial)'

    def add_arguments(self, parser):
        parser.add_argument('--retailer', choices=[*SCRAPERS, 'all'], default='all')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        retailer = options['retailer']
        dry_run = options['dry_run']
        targets = list(SCRAPERS.keys()) if retailer == 'all' else [retailer]

        async def run_all():
            tasks = [self._scrape(name, dry_run) for name in targets]
            return await asyncio.gather(*tasks)

        asyncio.run(run_all())

    async def _scrape(self, name: str, dry_run: bool):
        scraper = SCRAPERS[name]()
        try:
            products = await scraper.search_many(QUERIES)
        except Exception as exc:
            self.stderr.write(f'[{name}] Error: {exc}')
            return
        if dry_run:
            self.stdout.write(f'[{name}] {len(products)} productos encontrados (dry-run)')
        else:
            count = scraper.upsert_products(products)
            self.stdout.write(self.style.SUCCESS(f'[{name}] {count} upserted'))
