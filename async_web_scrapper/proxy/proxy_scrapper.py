import logging
import httpx
from .proxy_types import *
from .. import GenericScrapper, GenericPage, failsafe_request
from bs4 import BeautifulSoup
from enum import Enum


class PageEnum(Enum):
    SOCKS = 0
    HTTPS = 1
    ANON = 2
    UK = 3
    US = 4


class _ProxyPage:
    async def parse_entries(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(self.url)
            r.raise_for_status()
        
        html = BeautifulSoup(r.text, 'html.parser')
        return map(
            lambda x: list(map(lambda y: y.text.strip(), x.find_all('td'))), 
            html.find('table').find('tbody').find_all('tr')
        )


class SOCKSPage(GenericPage, _ProxyPage):
    @property
    @failsafe_request
    async def items(self):
        logging.info('Parsing page with SOCKS proxies')
        entries = await self.parse_entries()
        return list(map(lambda x: SOCKS4Proxy(*x[:3]) if x[4].lower() == 'socks4' else SOCKS5Proxy(*x[:3]), entries))


class HTTPSPage(GenericPage, _ProxyPage):
    @property
    @failsafe_request
    async def items(self):
        logging.info('Parsing page with HTTPS proxies')
        entries = await self.parse_entries()
        return list(map(lambda x: HTTPSProxy(*x[:3]), entries))


class AnonPage(GenericPage, _ProxyPage):
    @property
    @failsafe_request
    async def items(self):
        logging.info('Parsing page with anonymous proxies')
        entries = await self.parse_entries()
        return list(map(lambda x: HTTPSProxy(*x[:3]) if x[6].lower() == 'yes' else HTTPProxy(*x[:3]), entries))


class UKPage(AnonPage):
    pass


class USPage(AnonPage):
    pass


class ProxyScrapper(GenericScrapper):
    def BASE_URL(self, page):
        urls_dict = {
            PageEnum.SOCKS: 'https://www.socks-proxy.net/',
            PageEnum.HTTPS: 'https://www.sslproxies.org/',
            PageEnum.ANON: 'https://free-proxy-list.net/anonymous-proxy.html',
            PageEnum.UK: 'https://free-proxy-list.net/uk-proxy.html',
            PageEnum.US: 'https://www.us-proxy.org/'
        }
        return urls_dict[page]

    async def _pages_constructor(self):
        self.pages = [
            SOCKSPage(self.BASE_URL(PageEnum.SOCKS)),
            HTTPSPage(self.BASE_URL(PageEnum.HTTPS)),
            AnonPage(self.BASE_URL(PageEnum.ANON)),
            UKPage(self.BASE_URL(PageEnum.UK)),
            USPage(self.BASE_URL(PageEnum.US))
        ]
