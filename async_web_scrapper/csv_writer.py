import csv
import asyncio
import logging
from . import GenericItem


# TODO: delete csv if already exists on the startup
# TODO: backup csv when done
# it is not concurrent and never meant to be
class AsyncCSVWriter:
    # class constructor
    def __init__(self, csvpath: str):
        self.csvpath = csvpath
        self.__write_queue = asyncio.Queue()
        asyncio.create_task(self._start_writer())
    
    # append item to the csv
    async def add_item(self, item: GenericItem):
        await self.__write_queue.put(item)

    async def _start_writer(self):
        logging.info(f'Started AsyncCSVWriter with csvpath={self.csvpath}')
        while True:
            item = await self.__write_queue.get()
            with open(self.csvpath, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(item.to_csv_row())
