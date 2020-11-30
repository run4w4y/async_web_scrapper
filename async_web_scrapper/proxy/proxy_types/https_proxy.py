from ..proxy import Proxy


class HTTPSProxy(Proxy):
    @property
    def PROXY_PROTOCOL(self):
        return "https"
    
    def to_dict(self):
        return {
            'http': f'http://{self.ip}:{self.port}',
            'https': f'https://{self.ip}:{self.port}'
        }