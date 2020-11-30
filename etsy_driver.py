import httpx
import logging
from bs4 import BeautifulSoup
from async_web_scrapper import GenericScrapper, GenericItem, GenericPage 

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
    async def items(self):
        logging.info(self.url)

        async with httpx.AsyncClient(headers=HEADERS) as client:
            r = await client.get(self.url)
        
        html = BeautifulSoup(r.text, 'html.parser')
        found_items = html.find_all('a', attrs={'class': 'listing-link'})
        return list(map(
            lambda x: 
                EtsyItem(
                    x['title'], 
                    x['data-listing-id'], 
                    x.find('img')['srcset'].split(',')[1].split()[0].strip()
                ), 
                found_items
        ))


class EtsyScrapper(GenericScrapper):
    @staticmethod
    def BASE_URL(page):
        return f'https://www.etsy.com/shop/EvintageVeils/sold?ref=pagination&page={page}'
    
    async def _pages_constructor(self):
        async with httpx.AsyncClient(headers=HEADERS) as client:
            r = await client.get(self.BASE_URL(1))
            r.raise_for_status()

        html = BeautifulSoup(r.text, 'html.parser')
        limit = int(html.find('ul', attrs={'class': 'btn-group-md'}).find_all('a')[-2]['data-page'])
        logging.info(limit)
        self.pages = [EtsyPage(self.BASE_URL(i)) for i in range(1, limit + 1)]
