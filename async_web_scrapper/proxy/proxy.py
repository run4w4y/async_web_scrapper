from abc import ABC, abstractmethod
from async_web_scrapper import GenericItem
import logging
import httpx
import ssl


class Proxy(GenericItem, ABC):
    PING_URL = 'https://www.google.com/'
    
    @property
    @abstractmethod
    def PROXY_PROTOCOL(self):
        pass

    def __str__(self):
        return f'{self.PROXY_PROTOCOL}://{self.ip}:{self.port}'

    def __repr(self):
        return str(self)

    # class constructor, pretty much the same everywhere
    def __init__(self, ip: str, port: int, country: str = None):
        self.ip = ip
        self.port = port
        self.country = country
    
    # parse ip:port from a string
    @classmethod
    def parse(cls, proxy_str: str):
        proxy_str = proxy_str.strip() # strip the string just in case

        # check if the provided string is a valid ip:port
        if not re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+', proxy_str):
            raise InvalidIPStringError(f'String {proxy_str} is not a valid ip:port string')
        
        s = proxy_str.split(':')
        return cls(s[0], int(s[1]))
    
    # checks if proxy is available
    async def check(self) -> bool:
        try:
            async with httpx.AsyncClient(proxies=self.to_httpx()) as client:
                r = await client.get(self.PING_URL, timeout=20)
                
            # logging.info(f'Proxy {self} is available')
            return True
        except (httpx.HTTPError, ssl.SSLError) as e:
            # logging.warning(f'Proxy {self} seems to be unavailable')
            return False

    # converts proxy to a dict usable with requests
    def to_httpx(self):
        return httpx.Proxy(
            url = f'{self.PROXY_PROTOCOL}://{self.ip}:{self.port}',
            mode = 'FORWARD_ONLY'
        )
    
    # converts proxy to a csv row
    def to_csv_row(self) -> list:
        return [self.PROXY_PROTOCOL, self.ip, self.port, self.country]
