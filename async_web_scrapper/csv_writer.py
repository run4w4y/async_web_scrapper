import io
import csv
import asyncio
import aiofiles
import logging
import os.path
from . import GenericItem


class _JobDone:
    pass


# TODO: delete csv if already exists on the startup
# TODO: backup csv when done
# it is not concurrent and never meant to be
class AsyncCSVWriter:
    JOB_DONE = _JobDone()

    # class constructor
    def __init__(self, csvpath: str):
        self.existing_rows = []
        if os.path.exists(csvpath):
            with open(csvpath) as csvfile:
                reader = csv.reader(csvfile)
                self.existing_rows.extend(list(reader))

        self.csvpath = csvpath
        self.__write_queue = asyncio.Queue()
        self._writer_task = asyncio.create_task(self._start_writer())
    
    # append item to the csv
    async def add_item(self, item: GenericItem):
        await self.__write_queue.put(item)
    
    async def _write(self, item):
        async with aiofiles.open(self.csvpath, 'a', newline='') as csvfile:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(item.to_csv_row())
            await csvfile.write(buffer.getvalue())

    async def stop(self):
        await self.__write_queue.put(self.JOB_DONE)
        await self._writer_task

    async def _start_writer(self):
        logging.info(f'Started AsyncCSVWriter with csvpath={self.csvpath}')
        while True:
            try:
                item = await self.__write_queue.get()

                if item is self.JOB_DONE:
                    logging.info(f'AsyncCSVWriter(csvpath={self.csvpath}) done')
                    break 
                
                await self._write(item)
            except asyncio.CancelledError:
                logging.info(f'AsyncCSVWriter(csvpath={self.csvpath}) done')
