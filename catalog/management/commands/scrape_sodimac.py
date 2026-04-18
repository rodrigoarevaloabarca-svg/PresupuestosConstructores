import asyncio
from django.core.management.base import BaseCommand
from catalog.scrapers.sodimac import SodimacScraper

QUERIES = [
    'cemento', 'cañería', 'cable eléctrico', 'pintura',
    'llave paso', 'tomacorriente', 'teja', 'perno', 'silicon',
]


class Command(BaseCommand):
    help = 'Scrape productos de Sodimac.cl y los guarda en RetailerProduct'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Imprime sin guardar')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        scraper = SodimacScraper()
        products = asyncio.run(scraper.search_many(QUERIES))
        if dry_run:
            for p in products:
                self.stdout.write(f"[sodimac] {p['name']} — ${p['price_clp']:,}")
            self.stdout.write(f'Total: {len(products)} productos (dry-run, nada guardado)')
        else:
            count = scraper.upsert_products(products)
            self.stdout.write(self.style.SUCCESS(f'[Sodimac] {count} productos guardados/actualizados'))
