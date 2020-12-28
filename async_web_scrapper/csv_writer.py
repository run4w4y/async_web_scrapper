import io
import os
import csv
import trio
import math
import logging


class CSVWriter:
    def __init__(self, csvpath):
        # read existing rows first
        self.existing_rows = []
        if os.path.exists(csvpath):
            with open(csvpath) as csvfile:
                reader = csv.reader(csvfile)
                self.existing_rows.extend(list(reader))

        self.csvpath = csvpath
        # open channel to store items in
        self.__write_send_channel, self.__write_receive_channel = trio.open_memory_channel(math.inf)
    
    # add items to the channel
    async def add_item(self, item):
        await self.__write_send_channel.send(item)

    # write function to be used in writer
    async def _write(self, item):
        async with await trio.open_file(self.csvpath, 'a', newline='') as csvfile:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(item.to_csv_row())
            await csvfile.write(buffer.getvalue())

    # starts the writer
    async def start(self, task_status=trio.TASK_STATUS_IGNORED):
        # open up cancel scope so we can cancel the task if needed
        with trio.CancelScope() as scope:
            task_status.started(scope)
            logging.info(f'Started CSVWriter with csvpath={self.csvpath}')

            # the writer part
            while True:
                item = await self.__write_receive_channel.receive()
                await self._write(item)
        # log when out of cancel scope
        logging.info(f'CSVWriter(csvpath={self.csvpath}) done')
