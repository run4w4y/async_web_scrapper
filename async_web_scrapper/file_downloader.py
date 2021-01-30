import os
import trio
import math
import httpx
import shutil
import logging


class _JobDone:
    pass


class FileDownloader:
    _JOB_DONE_SIGNAL = _JobDone()

    def __init__(self, retriever, save_path='downloads/', workers_amount=10, useproxy=False, check_request=None, after_download=None):
        self.retriever = retriever
        self.save_path = save_path
        self.useproxy = useproxy
        self.check_request = check_request # sync check 
        self.after_download = after_download # async operation

        # create path if doesnt exist
        os.makedirs(self.save_path, exist_ok=True)
        
        # channel with urls to snatch
        self.workers_amount = workers_amount
        self.__downloads_send_channel, self.__downloads_receive_channel = trio.open_memory_channel(math.inf)
        self.__done_send_channel, self.__done_receieve_channel = trio.open_memory_channel(0)

    # add downloads to the channel, returns the path where it will be saved
    async def add_download(self, download_url, filename=None):
        path = ""
        if filename is None:
            path = os.path.join(self.save_path, download_url.split('/')[-1].split('?')[0])
        else:
            path = os.path.join(self.save_path, filename)
        await self.__downloads_send_channel.send((path, download_url))
        return path

    async def _download(self, path, url):
        while True:
            r = await self.retriever.retrieve(url, failsafe=True, useproxy=self.useproxy)

            if self.check_request is not None and self.check_request(r):
                break
            elif self.check_request is None:
                break
            else:
                logging.error(f'Request check failed for download {url}. Trying again')

        async with await trio.open_file(path, 'wb') as f:
            await f.write(r.content)
        
        if self.after_download is not None:
            await self.after_download(path)

    # dispatched downloader task
    async def _dispatched_downloader(self, number=0, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started(scope)
            logging.info(f'Started dispatched downloader #{number}')

            while True:
                path, url = await self.__downloads_receive_channel.receive()

                if path is self._JOB_DONE_SIGNAL:
                    await self.__downloads_send_channel.send([self._JOB_DONE_SIGNAL]*2)
                    break

                logging.info(f'Downloading {url}')
                await self._download(path, url)

    # stops dispatched downloaders after they are done
    async def stop_when_done(self):
        await self.__downloads_send_channel.send([self._JOB_DONE_SIGNAL]*2)
        await self.__done_receieve_channel.receive()

    # downloader parent task
    async def start(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            # start nursery
            async with trio.open_nursery() as nursery:
                children = [await nursery.start(self._dispatched_downloader, i) for i in range(self.workers_amount)]

                task_status.started(scope)
                logging.info(f'Started FileDownloader with save_path={self.save_path}')
            await self.__done_send_channel.send(True)

        logging.info(f'FileDownloader(save_path={self.save_path}) done')
