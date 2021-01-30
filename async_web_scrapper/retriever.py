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
            return (None, httpx.AsyncClient(headers=self.HEADERS))
        else:
            proxy = await proxy_pool.get_proxy()
            return (proxy, httpx.AsyncClient(headers=self.HEADERS, proxies=proxy.to_httpx()))
    
    async def _retrieve(self, url, client, timeout, failsafe=False, data=None):
        r = None
        while True:
            try:
                async with client[1]:
                    r = None
                    if data is None:
                        r = await client[1].get(url, timeout=timeout)
                    else:
                        r = await client[1].post(url, timeout=timeout, data=data)
                    if r.status_code == 404:
                        return None
                    if r.status_code == 429:
                        self.proxy_pool.mark_dead_proxy(client[0]) # supposedly that works
                    r.raise_for_status()
            except (httpx.ProxyError, ssl.SSLError, httpx.HTTPError, httpx.ReadError, httpx.ConnectTimeout, OSError) as e:
                # logging.error(e)
                if failsafe:
                    continue
                raise e
            else:
                break
        
        return r
    
    async def retrieve(self, url, useproxy=True, timeout=10, failsafe=False, data=None):
        client = None
        if useproxy and self.proxy_pool is not None:
            client = await self._client(self.proxy_pool) 
        else:
            client = await self._client()
        
        result_send_channel, result_receive_channel = trio.open_memory_channel(0)
        await self._retrieve_send_channel.send((url, result_send_channel, client, timeout, failsafe, data))
        result = await result_receive_channel.receive()
        
        await result_receive_channel.aclose()
        await result_send_channel.aclose()
        
        return result

    async def retrieve_html(self, url, useproxy=True, timeout=10, failsafe=False, data=None):
        r = await self.retrieve(url, useproxy, timeout, failsafe, data)
        
        if r is None:
            return None
        
        return BeautifulSoup(r.text, 'html.parser')

    async def retrieve_text(self, url, useproxy=True, timeout=10, failsafe=False, data=None):
        r = await self.retrieve(url, useproxy, timeout, failsafe, data)

        if r is None:
            return None

        return r.text

    async def _dispatched_retriever(self, number=0, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started(scope)
            logging.info(f'Started dispatched Retriever #{number}')

            while True:
                url, result_channel, client, timeout, failsafe, data = await self._retrieve_receive_channel.receive()
                r = await self._retrieve(url, client, timeout, failsafe, data)
                await result_channel.send(r)

    async def start(self, task_status=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            async with trio.open_nursery() as nursery:
                children = [await nursery.start(self._dispatched_retriever, i) for i in range(self.workers_amount)]

                task_status.started(scope)
                logging.info(f'Started Retriever')
