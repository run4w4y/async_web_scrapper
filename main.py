import asyncio
import logging
from async_web_scrapper.proxy import ProxyScrapper, ProxyPool
from etsy_driver import EtsyScrapper

async def main():
    proxy_pool = ProxyPool(scrapper=ProxyScrapper(csvpath='proxies.csv'))
    scrapper = EtsyScrapper(csvpath='items.csv', proxy_pool=proxy_pool)
    await scrapper.result

if __name__ == '__main__':
    asyncio.log.logger.setLevel(logging.ERROR)
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
    logging.info('Starting scrapper')
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Finishing up...')