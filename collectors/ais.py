import asyncio

from dataclasses import dataclass
from .parser.base import BaseParser
from lxml import etree


@dataclass
class AisUser:
    name: str
    ais_id : int

class AisParser(BaseParser):
    def __init__(self, loop: asyncio.AbstractEventLoop, login: str = None, password: str = None) -> None:
        super().__init__(loop)
        self._login: str = login
        self._password: str = password
    
    async def login(self) -> None:
        cookies = {
            '_ga': 'GA1.2.798688000.1658932723',
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Origin': 'https://is.stuba.sk',
            'Referer': 'https://is.stuba.sk/system/login.pl?odhlasen=1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        data = {
            'login_hidden': '1',
            'destination': '/auth/?lang=en',
            'auth_id_hidden': '0',
            'auth_2fa_type': 'no',
            'credential_0': self._login,
            'credential_1': self._password,
            'credential_k': '',
            'credential_2': '86400',
        }

        async with self._session.post('https://is.stuba.sk/system/login.pl', cookies=cookies, headers=headers, data=data, allow_redirects=False) as response:
            return response.status == 302
        return False
    
    async def get_user_data(self):
        async with self._session.get('https://is.stuba.sk/auth/kontrola/') as response:
            dom = etree.HTML(await response.text())
        
        return AisUser(
            name=dom.xpath('//*[@id="tmtab_1"]/tbody/tr[1]/td[2]/text()')[0],
            ais_id=int(dom.xpath('//*[@id="tmtab_1"]/tbody/tr[2]/td[2]/text()')[0]))
