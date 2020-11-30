from abc import ABC, abstractmethod
from .file_downloader import AsyncFileDownloader


class GenericPage(ABC):
    def __init__(self, url: str, proxy_pool = None, downloader: AsyncFileDownloader = None):
        self.url = url
        self.proxy_pool = proxy_pool
        self.downloader = downloader
    
    @property
    @abstractmethod
    async def items(self):
        pass
