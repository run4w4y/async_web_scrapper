from ..proxy import Proxy


class HTTPProxy(Proxy):
    @property
    def PROXY_PROTOCOL(self):
        return "http"