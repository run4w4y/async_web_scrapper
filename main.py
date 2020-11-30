import asyncio
import logging
from async_web_scrapper.proxy import ProxyScrapper

async def main():
    scrapper = ProxyScrapper(csvpath='items.csv')
    await scrapper.task_result
    print(scrapper.result)

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
    logging.info('Starting scrapper')
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Finishing up...')