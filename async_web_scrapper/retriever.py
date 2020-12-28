import ssl
import math
import trio
import httpx
import logging
from bs4 import BeautifulSoup


class Retriever:
    # fake User-Agent
    HEADERS = {
        'User-Agent': 
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'
    }

    def __init__(self, proxy_pool=None, workers_amount=10):
        self.proxy_pool = proxy_pool
        self.workers_amount = workers_amount
        self._retrieve_send_channel, self._retrieve_receive_channel = trio.open_memory_channel(math.inf)
    
    async def _client(self, proxy_pool=None):
        if proxy_pool is None:
            return httpx.AsyncClient(headers=self.HEADERS)
        else:
            proxy = await proxy_pool.get_proxy()
            return httpx.AsyncClient(headers=self.HEADERS, proxies=proxy.to_httpx())
    
    async def _retrieve(self, url, client, timeout, failsafe=False):
        r = None
        while True:
            try:
                async with client:
                    r = await client.get(url, timeout=timeout)
                    r.raise_for_status()
            except (ssl.SSLError, httpx.HTTPError, httpx.ReadError, httpx.ConnectTimeout, OSError) as e:
                if failsafe:
                    continue
                raise e
            else:
                break
        
        return r
    
    async def retrieve(self, url, useproxy=True, timeout=10, failsafe=False):
        client = None
        if useproxy and self.proxy_pool is not None:
            client = await self._client(self.proxy_pool) 
        else:
            client = await self._client()
        
        result_send_channel, result_receive_channel = trio.open_memory_channel(0)
        await self._retrieve_send_channel.send((url, result_send_channel, client, timeout, failsafe))
        result = await result_receive_channel.receive()
        
        await result_receive_channel.aclose()
        await result_send_channel.aclose()
        
        return result

    async def retrieve_html(self, url, useproxy=True, timeout=10, failsafe=False):
        r = await self.retrieve(url, useproxy, timeout, failsafe)
        return BeautifulSoup(r.text, 'html.parser')

    async def retrieve_text(self, url, useproxy=True, timeout=10, failsafe=False):
        r = await self.retrieve(url, useproxy, timeout, failsafe)
        return r.text

    async def _dispatched_retriever(self, number=0, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started(scope)
            logging.info(f'Started dispatched Retriever #{number}')

            while True:
                url, result_channel, client, timeout, failsafe = await self._retrieve_receive_channel.receive()
                r = await self._retrieve(url, client, timeout, failsafe)
                await result_channel.send(r)

    async def start(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            async with trio.open_nursery() as nursery:
                children = [await nursery.start(self._dispatched_retriever, i) for i in range(self.workers_amount)]

                task_status.started(scope)
                logging.info(f'Started Retriever')