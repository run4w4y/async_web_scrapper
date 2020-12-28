import trio
import math
import logging
from . import CSVWriter, FileDownloader
from abc import ABC, abstractmethod


class GenericScrapper(ABC):
    def __init__(self, retriever, csv_writer=None, downloader=None, workers_amount=10):
        self.retriever = retriever
        self.csv_writer = csv_writer
        self.downloader = downloader
        self.workers_amount = workers_amount

        self._used_pages = set()
        self._pages_set = set()
        self._page_send_channel, self._page_receive_channel = trio.open_memory_channel(math.inf)
        self._result_send_channel, self.result_receive_channel = trio.open_memory_channel(math.inf)
        self._done_send_channel, self._done_receive_channel = trio.open_memory_channel(0)

    @property
    @abstractmethod
    async def pages(self):
        pass

    @property
    async def done(self):
        await self._done_receive_channel.receive()
        # close the channel
        await self._done_receive_channel.aclose()

    async def _wait_till_done(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started()
            
            while self._pages_set != self._used_pages:
                await trio.sleep(1.5)

            await self._done_send_channel.send(True)

    async def _dispatched_scrapper(self, number=0, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started(scope)
            logging.info(f'Started dispatched {type(self).__name__} #{number}')

            while True:
                page = await self._page_receive_channel.receive()
                res = await page.process()
                
                for page in res.pages:
                    self._pages_set.add(page)
                    await self._page_send_channel.send(page)
                
                for item in res.items:
                    if self.csv_writer is not None:
                        await self.csv_writer.add_item(item)
                    await self._result_send_channel.send(item)
                
                for download in res.downloads:
                    if self.downloader is not None:
                        await self.donwloader.add_download(download)
                
                self._used_pages.add(page)
        
        logging.info(f'Dispatched {type(self).__name__} #{number} done')

    async def start(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            start_pages = await self.pages
            for page in start_pages:
                self._pages_set.add(page)
                await self._page_send_channel.send(page)

            async with trio.open_nursery() as nursery:
                children_scopes = [
                    await nursery.start(self._dispatched_scrapper, i) 
                for i in range(self.workers_amount)]

                task_status.started(scope)
                logging.info(f'Started {type(self).__name__}')
                
                await nursery.start(self._wait_till_done)

        # close all the channels when we are done
        await self._page_send_channel.aclose()
        await self._page_receive_channel.aclose()
        await self._result_send_channel.aclose()
        await self._done_send_channel.aclose()

        # cancel children
        for scope in children_scopes:
            scope.cancel()
        
        logging.info(f'{type(self).__name__} done')
