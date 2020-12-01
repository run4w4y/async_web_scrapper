import httpx
import logging
from bs4 import BeautifulSoup
from async_web_scrapper import GenericScrapper, GenericItem, GenericPage, failsafe_request

HEADERS = {
    'User-Agent': 
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'
}


class EtsyItem(GenericItem):
    def __init__(self, title: str, listing_id: str, image_url: str):
        self.title = title
        self.listing_id = listing_id
        self.image_url = image_url
    
    def to_csv_row(self):
        return [self.title, self.listing_id, self.image_url]


class EtsyPage(GenericPage):
    @property
    @failsafe_request
    async def items(self):
        logging.info(self.url)

        r = None
        if self.proxy_pool is not None:
            proxy = await self.proxy_pool.get_proxy()
            async with httpx.AsyncClient(headers=HEADERS, proxies=proxy.to_httpx()) as client:
                r = await client.get(self.url, timeout=12)
        else:
            async with httpx.AsyncClient(headers=HEADERS) as client:
                r = await client.get(self.url, timeout=12)
        
        html = BeautifulSoup(r.text, 'html.parser')
        found_items = html.find_all('a', attrs={'class': 'listing-link'})

        res = []
        for i in found_items:
            item = EtsyItem(
                i['title'], 
                i['data-listing-id'], 
                i.find('img')['srcset'].split(',')[1].split()[0].strip()
            )
            # logging.info(f'Added {item.image_url} to download queue')
            await self.downloader.add_download(item.image_url)
            res.append(item)

        return res


class EtsyScrapper(GenericScrapper):
    @staticmethod
    def BASE_URL(page):
        return f'https://www.etsy.com/shop/EvintageVeils/sold?ref=pagination&page={page}'
    
    @failsafe_request
    async def __get_limit(self):
        r = None
        if self.proxy_pool is not None:
            proxy = await self.proxy_pool.get_proxy()
            async with httpx.AsyncClient(headers=HEADERS, proxies=proxy.to_httpx()) as client:
                r = await client.get(self.BASE_URL(1), timeout=12)
        else:
            logging.warning('ProxyPool is None')
            async with httpx.AsyncClient(headers=HEADERS) as client:
                r = await client.get(self.BASE_URL(1), timeout=12)
        r.raise_for_status()

        html = BeautifulSoup(r.text, 'html.parser')
        return int(html.find('ul', attrs={'class': 'btn-group-md'}).find_all('a')[-2]['data-page'])

    async def _pages_constructor(self):
        limit = await self.__get_limit()
        logging.info(limit)
        self.pages = [EtsyPage(self.BASE_URL(i), proxy_pool=self.proxy_pool, downloader=self.downloader) for i in range(1, limit + 1)]
