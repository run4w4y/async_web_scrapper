from abc import ABC, abstractmethod


class GenericPage(ABC):
    def __init__(self, url: str):
        self.url = url
    
    @property
    @abstractmethod
    async def items(self):
        pass
