import httpx

from .base import BaseRetailerScraper

SEARCH_URL = "https://www.sodimac.com/sodimac-cl/search?Ntt={query}&No=0&Nrpp=48&content="


class SodimacScraper(BaseRetailerScraper):
    retailer_slug = "sodimac"

    async def search(self, q: str) -> list[dict]:
        url = SEARCH_URL.format(query=q)
        async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for p in data.get("products", []):
            try:
                price = p.get("price", {})
                min_price = price.get("minPrice") or price.get("offerPrice") or price.get("normalPrice")
                if not min_price:
                    continue
                results.append(
                    {
                        "name": p.get("displayName", ""),
                        "price_clp": int(min_price),
                        "url": p.get("url", ""),
                        "sku": p.get("sku") or p.get("productId", ""),
                        "category": p.get("categoryName", ""),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        return results
