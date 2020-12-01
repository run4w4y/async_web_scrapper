import httpx
import asyncio
import logging
import ssl
from .csv_writer import AsyncCSVWriter
from abc import ABC, abstractmethod
from .exceptions import ImproperInitError
from .file_downloader import AsyncFileDownloader


class _JobDone:
    pass


def failsafe_request(f):
    async def wrapped(*args, **kwargs):
        res = None
        while True:
            try:
                logging.info('failed retrieving the page')
                res = await f(*args, **kwargs)
            except (ssl.SSLError, httpx.HTTPError):
                continue
            else:
                break
        return res

    return wrapped


# TODO: make use of file downloader
# TODO: make use of proxy pool
class GenericScrapper(ABC):
    JOB_DONE = _JobDone()

    @staticmethod
    @abstractmethod
    def BASE_URL(page):
        pass
    
    @abstractmethod
    async def _pages_constructor(self):
        pass
    
    # if proxy_pool is None scrapper is not going to be using any proxies
    # if csvpath is None scrapper is not going to be writing results to csv
    def __init__(self, workers_amount: int = 10, proxy_pool = None, csvpath: str = None):
        self.proxy_pool = proxy_pool
        self.csvpath = csvpath
        self.workers_amount = workers_amount
        
        self.__page_queue = asyncio.Queue(maxsize=self.workers_amount)
        self.__result_queue = asyncio.Queue()
        self.__result = []
        self.pages = None

        self.__csv_writer = None
        if self.csvpath is not None:
            self.__csv_writer = AsyncCSVWriter(csvpath)
        
        self.downloader = AsyncFileDownloader(workers_amount=15)

        self.task_parser = asyncio.create_task(self._start_parser())
        self.task_result = asyncio.create_task(self._result_writer())
        self.tasks_dispatched = [asyncio.create_task(self._dispatched_parser(i)) for i in range(workers_amount)]

    @property
    async def result(self):
        await self.task_result
        return self.__result

    async def _result_writer(self):
        while True:
            res = await self.__result_queue.get()
            if res is self.JOB_DONE:
                break

            self.__result.extend(res)

    async def _start_parser(self):
        await self._pages_constructor()
        
        if self.pages is None:
            raise ImproperInitError('Object self.pages was not initialized properly. Make sure to fill it in on startup.')
        
        for page in self.pages:
            await self.__page_queue.put(page)
        
        # end dispatched tasks
        await self.__page_queue.put(self.JOB_DONE)
        await asyncio.gather(*self.tasks_dispatched)
        # end result writer
        await self.__result_queue.put(self.JOB_DONE)
        await self.task_result

    async def _dispatched_parser(self, number):
        while True:
            page = await self.__page_queue.get()
            if page is self.JOB_DONE:
                await self.__page_queue.put(self.JOB_DONE)
                break
            
            res = await page.items
            logging.info('Got page contents, writing to csv')
            if self.__csv_writer is not None:
                for item in res:
                    await self.__csv_writer.add_item(item)
            
            await self.__result_queue.put(res)
