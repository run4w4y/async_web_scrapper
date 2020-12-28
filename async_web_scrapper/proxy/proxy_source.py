from abc import ABC, abstractmethod


class ProxySource(ABC):
    @abstractmethod
    async def get_proxies(self):
        pass