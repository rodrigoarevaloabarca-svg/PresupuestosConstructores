import httpx
from bs4 import BeautifulSoup
from .base import BaseRetailerScraper

SEARCH_URL = 'https://www.imperial.cl/search?q={query}'


class ImperialScraper(BaseRetailerScraper):
    retailer_slug = 'imperial'

    async def search(self, q: str) -> list[dict]:
        url = SEARCH_URL.format(query=q)
        async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, 'lxml')
        results = []

        for item in soup.select('.product-item, .product-grid-item, [data-product-id]'):
            try:
                name_el = item.select_one('.product-name, .product-title, h2, h3')
                price_el = item.select_one('.price, .product-price, [class*="price"]')
                link_el = item.select_one('a[href]')
                if not name_el or not price_el:
                    continue
                name = name_el.get_text(strip=True)
                raw_price = price_el.get_text(strip=True).replace('$', '').replace('.', '').replace(',', '').strip()
                price = int(''.join(filter(str.isdigit, raw_price)) or 0)
                if not price:
                    continue
                href = link_el['href'] if link_el else ''
                if href and not href.startswith('http'):
                    href = 'https://www.imperial.cl' + href
                results.append({'name': name, 'price_clp': price, 'url': href, 'sku': None})
            except (ValueError, TypeError, AttributeError):
                continue
        return results
