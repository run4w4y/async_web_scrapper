import re
import httpx
from abc import ABC, abstractmethod
from async_web_scrapper import GenericItem
from .exceptions import InvalidIPStringError


class Proxy(GenericItem, ABC):
    @property
    @abstractmethod
    def PROXY_PROTOCOL(self):
        pass

    def __str__(self):
        return f'{self.PROXY_PROTOCOL}://{self.ip}:{self.port}'

    def __repr(self):
        return str(self)
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __hash__(self):
        return hash(str(self))

    # class constructor, pretty much the same everywhere
    def __init__(self, ip: str, port: int, country: str = None, username=None, password=None):
        self.ip = ip
        self.port = port
        self.country = country
        self.username = username
        self.password = password
    
    # parse ip:port from a string
    @classmethod
    def parse(cls, proxy_str: str, username=None, password=None):
        proxy_str = proxy_str.strip() # strip the string just in case

        # check if the provided string is a valid ip:port
        if not re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+', proxy_str):
            raise InvalidIPStringError(f'String {proxy_str} is not a valid ip:port string')
        
        s = proxy_str.split(':')
        return cls(s[0], int(s[1]))

    # converts proxy to a dict usable with requests
    def to_httpx(self):
        return httpx.Proxy(
            url = f'{self.PROXY_PROTOCOL}://{self.ip}:{self.port}' if self.username is None 
                else f'{self.PROXY_PROTOCOL}://{self.username}:{self.password}@{self.ip}:{self.port}',
            mode = 'TUNNEL_ONLY', # mode=tunnel so we can use https even through http proxies
        )
    
    # converts proxy to a csv row
    def to_csv_row(self) -> list:
        return [self.PROXY_PROTOCOL, self.ip, self.port, self.country]
