import ssl
import trio
import math
import httpx
import logging
from .proxy import Proxy
from .proxy_source import ProxySource
from .proxy_types import HTTPProxy, HTTPSProxy


# TODO: [+] implement good proxy cooldown
# TODO: [+] check if its possible to use http proxies too
# TODO: [ ] might want to preserve sessions if that would help stay connection to a proxy alive
class ProxyPool:
    def __init__(self, source: ProxySource, workers_amount=10, ping_url='https://www.google.com/', update_period=120, cooldown=0):
        self.source = source
        self.workers_amount = workers_amount
        self.ping_url = ping_url
        self.update_period = update_period
        self.cooldown = cooldown
        self._proxy_set = set()
    
        self._good_send_channel, self._good_receive_channel = trio.open_memory_channel(math.inf)
        self._bad_send_channel, self._bad_receive_channel = trio.open_memory_channel(math.inf)
        self._hold_send_channel, self._hold_receive_channel = trio.open_memory_channel(math.inf)
    
    async def add_proxy(self, proxy: HTTPSProxy):
        await self._bad_send_channel.send(proxy)
        self._proxy_set.add(proxy)
    
    # get a working proxy from the queue
    async def get_proxy(self):
        proxy = await self._good_receive_channel.receive()
        await self._hold_send_channel.send(proxy)
        return proxy
    
    # check proxy for availability
    async def _check_proxy(self, proxy):
        try:
            async with httpx.AsyncClient(proxies=proxy.to_httpx()) as client:
                r = await client.get(self.ping_url, timeout=10)
            # logging.info(f'Proxy {proxy} appears to be working')
            return True
        except (httpx.HTTPError, ssl.SSLError, httpx.ReadError, httpx.ConnectTimeout, OSError) as e:
            # logging.info(f'Proxy {proxy} does not seem to be working')
            return False
    
    async def _dispatched_checker(self, number=0, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started(scope)
            logging.info(f'Started dispatched proxy checker #{number}')

            while True:
                proxy = await self._bad_receive_channel.receive()
                if await self._check_proxy(proxy):
                    await self._good_send_channel.send(proxy)
                else:
                    await self._bad_send_channel.send(proxy)
        
        logging.info(f'Dispatched proxy checker #{number} done')
    
    async def update_proxies(self):
        proxies = await self.source.get_proxies()
        
        count = 0
        for proxy in filter(lambda x: isinstance(x, (HTTPSProxy, HTTPProxy)) and x not in self._proxy_set, proxies):
            await self.add_proxy(proxy)
            count += 1
        
        logging.info(f'Added {count} proxies to the pool')

    async def _proxy_updater(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started()
            logging.info('Started proxy updater')

            while True:
                await self.update_proxies()
                await trio.sleep(self.update_period)
    
    async def _proxy_holder(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started()
            
            while True:
                proxy = await self._hold_receive_channel.receive()
                logging.info(f'Proxy {proxy} is on hold')
                await trio.sleep(self.cooldown)
                await self._bad_send_channel.send(proxy)

    async def start(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            async with trio.open_nursery() as nursery:
                updater = await nursery.start(self._proxy_updater)
                children = [await nursery.start(self._dispatched_checker, i) for i in range(self.workers_amount)]
                holders = [await nursery.start(self._proxy_holder) for i in range(100)] # spawn 100 holders

                task_status.started(scope)
                logging.info(f'Started ProxyPool')
        
        logging.info(f'ProxyPool done')
