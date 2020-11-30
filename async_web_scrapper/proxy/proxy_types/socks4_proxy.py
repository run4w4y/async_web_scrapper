from ..proxy import Proxy


class SOCKS4Proxy(Proxy):
    @property
    def PROXY_PROTOCOL(self):
        return "socks4"