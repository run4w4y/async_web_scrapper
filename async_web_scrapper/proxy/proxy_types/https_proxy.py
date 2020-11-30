import httpx
from ..proxy import Proxy


class HTTPSProxy(Proxy):
    @property
    def PROXY_PROTOCOL(self):
        return "https"

    def to_httpx(self):
        return httpx.Proxy(
            url = f'http://{self.ip}:{self.port}',
            mode = 'TUNNEL_ONLY'
        )