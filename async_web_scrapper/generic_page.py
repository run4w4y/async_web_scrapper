import httpx
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod


class PageResult:
    def __init__(self, items=[], pages=[], downloads=[], csvpath=None):
        self.items = items
        self.pages = pages
        self.downloads = downloads
        self.csvpath = csvpath


class GenericPage(ABC):
    def __eq__(self, other):
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)

    def __init__(self, url, retriever, downloader=None):
        self.url = url
        self.retriever = retriever
        self.downloader = downloader

    @abstractmethod
    async def process(self) -> PageResult:
        pass
