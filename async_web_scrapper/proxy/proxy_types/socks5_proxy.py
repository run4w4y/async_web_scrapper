from ..proxy import Proxy


class SOCKS5Proxy(Proxy):
    @property
    def PROXY_PROTOCOL(self):
        return "socks5"