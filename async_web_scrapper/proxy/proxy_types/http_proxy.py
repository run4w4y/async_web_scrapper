from ..proxy import Proxy


class HTTPProxy(Proxy):
    PING_URL = 'http://www.google.com/'

    @property
    def PROXY_PROTOCOL(self):
        return "http"