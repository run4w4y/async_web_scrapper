import asyncio
import httpx
import shutil
import aiofiles
import os


class AsyncFileDownloader:
    def __init__(self, save_path: str = 'donwloads/', workers_amount: int = 10):
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)
        self.workers_amount = workers_amount

        self.__download_queue = asyncio.Queue(maxsize=self.workers_amount)
        self.tasks_dispatched = [self._downloader_dispatched(i) for i in range(self.workers_amount)]
    
    async def add_download(self, url: str):
        await self.__download_queue.put(url)
    
    async def _downloader_dispatched(self, number: int):
        while True:
            url = await self.__download_queue.get()
            filename = url.split('/')[-1]

            r = await httpx.get(url)
            r.raise_for_status()

            async with aiofiles.open(os.path.join(self.save_path, filename), 'wb') as f:
                await f.write(r.content)