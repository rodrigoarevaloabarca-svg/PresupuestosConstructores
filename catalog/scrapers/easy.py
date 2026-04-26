import httpx

from .base import BaseRetailerScraper

SEARCH_URL = "https://www.easy.cl/api/catalog_system/pub/products/search?ft={query}&_from={start}&_to={end}&O=OrderByScoreDESC"
PAGE_SIZE = 48


class EasyScraper(BaseRetailerScraper):
    retailer_slug = "easy"

    async def search(self, q: str) -> list[dict]:
        results = []
        start = 0
        async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
            while True:
                url = SEARCH_URL.format(query=q, start=start, end=start + PAGE_SIZE - 1)
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                for p in data:
                    try:
                        offer = p["items"][0]["sellers"][0]["commertialOffer"]
                        price = offer.get("Price") or offer.get("ListPrice")
                        if not price:
                            continue
                        results.append(
                            {
                                "name": p.get("productName", ""),
                                "price_clp": int(price),
                                "url": p.get("link", ""),
                                "sku": p["items"][0].get("itemId", ""),
                                "category": p.get("categories", [""])[0].split("/")[-2] if p.get("categories") else "",
                            }
                        )
                    except (KeyError, IndexError, TypeError, ValueError):
                        continue
                if len(data) < PAGE_SIZE:
                    break
                start += PAGE_SIZE
        return results
