import asyncio
import logging
from . import Proxy
from . import ProxyScrapper
from .proxy_types import HTTPSProxy


# TODO: check
class ProxyPool:
    # class constructor
    # proxies - list of HTTPSProxy
    # used_timeout - timeout for used proxies
    def __init__(self,
                 proxies: list = [],
                 used_timeout: int = 21600,
                 dispatched_amount: int = 10,
                 scrapper: ProxyScrapper = None):
        self.USED_TIMEOUT = used_timeout
        self.proxies = proxies
        self.scrapper = scrapper

        # queue for supposedly available proxies
        self.__good_queue = asyncio.Queue()
        # queue for supposedly unavailable proxies
        self.__bad_queue = asyncio.Queue()
        # queue for used proxies
        self.__used_queue = asyncio.Queue()
        # queue to be checked
        self.__check_queue = asyncio.Queue(maxsize=dispatched_amount)

        self.task_init = asyncio.create_task(self._init_queue())
        self.task_checker = asyncio.create_task(self._start_checker())
        self.task_renewer = asyncio.create_task(self._start_renewer())
        self.task_checkers_dispatched = [
            asyncio.create_task(self._checker_dispatched(i))
        for i in range(dispatched_amount)]

    # init a ProxyPool object using a file with proxies
    @classmethod
    def init_from_file(cls, path: str):
        with open(path) as f:
            proxies = list(map(Proxy.parse, f.readlines()))
            return cls(proxies)

    # adds proxy to the queue
    async def add_proxy(self, proxy: Proxy):
        await self.__bad_queue.put(proxy)

    # init the bad_queue
    async def _init_queue(self):
        if self.scrapper is not None:
            proxies_all = await self.scrapper.result
            self.proxies = list(filter(lambda x: isinstance(x, HTTPSProxy), proxies_all))
        
        logging.info(f'Initializing ProxyPool with {len(self.proxies)} proxies')
        for proxy in self.proxies:
            await self.add_proxy(proxy)

    # starts the process of checking all the proxies
    async def _start_checker(self):
        logging.info('Proxy checker started')
        while True:
            proxy = await self.__bad_queue.get()
            await self.__check_queue.put(proxy)

    # dispatched checker for concurrency
    async def _checker_dispatched(self, number: int):
        logging.info(f'Started dispatched proxy checker {number}')
        while True:
            proxy = await self.__check_queue.get()
            if await proxy.check():
                await self.__good_queue.put(proxy)
            else:
                await self.__bad_queue.put(proxy)

    # renews used proxies when timeout runs out
    async def _start_renewer(self):
        await self.task_init
        logging.info('Proxy renewer started')
        counter = dict.fromkeys(self.proxies, 0)
        
        while True:
            proxy = await self.__used_queue.get()
            counter[proxy] += 1
            if counter[proxy] >= 50:
                asyncio.create_task(self._hold_proxy(proxy))
            else:
                await self.__good_queue.put(proxy)
    
    async def _hold_proxy(self, proxy):
        logging.info(f'Proxy {proxy} is on hold')
        await asyncio.sleep(self.USED_TIMEOUT)
        await self.__bad_queue.put(proxy)

    # generator that yields a supposedly available proxy
    async def get_proxy(self) -> Proxy:
        proxy = await self.__good_queue.get()
        await self.__used_queue.put(proxy)
        return proxy
