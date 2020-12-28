import httpx
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod


class PageResult:
    def __init__(self, items=[], pages=[], downloads=[]):
        self.items = items
        self.pages = pages
        self.downloads = downloads


class GenericPage(ABC):
    def __init__(self, url, retriever, downloader=None):
        self.url = url
        self.retriever = retriever
        self.downloader = downloader

    @abstractmethod
    async def process(self) -> PageResult:
        pass
