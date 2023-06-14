"""
MIT License

Copyright (c) 2023 Illia Chaban

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio

from dataclasses import dataclass
from .parser.base import BaseParser
from lxml import etree


@dataclass
class AisUser:
    name: str
    ais_id : int

@dataclass
class AisUniversityNetwork:
    login: str
    password: str


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
    
    async def get_user_data(self) -> AisUser:
        async with self._session.get('https://is.stuba.sk/auth/kontrola/') as response:
            dom = etree.HTML(await response.text())
        
        return AisUser(
            name=dom.xpath('//*[@id="tmtab_1"]/tbody/tr[1]/td[2]/text()')[0],
            ais_id=int(dom.xpath('//*[@id="tmtab_1"]/tbody/tr[2]/td[2]/text()')[0]))
    
    async def get_university_network(self) -> AisUniversityNetwork:
        async with self._session.get('https://is.stuba.sk/auth/wifi/heslo_vpn_sit.pl') as response:
            dom = etree.HTML(await response.text())
        
        login = dom.xpath('//tbody/tr[1]/td[2]/b/text()')[0]
        password = dom.xpath('//tbody/tr[2]/td[2]/b/text()')[0]

        return AisUniversityNetwork(login=login, password=password)
    
    async def get_study_schedule(self) -> str:
        ais_id = (await self.get_user_data()).ais_id
        data = {
            'lang': 'sk',
            'rozvrh_student': ais_id,
            'rezervace': '0',
            'poznamky_base': '1',
            'poznamky_zmeny': '1',
            'poznamky_parovani': '1',
            'poznamky_dalsi_ucit': '1',
            'poznamky_jiny_areal': '1',
            'poznamky_dl_omez': '1',
            'typ_vypisu': 'souhrn',
            'konani_od': '12.09.2022',
            'konani_do': '18.09.2022',
            'format': 'pdf',
            'nezvol_all': '1',
            'poznamky': '1',
            'zobraz': '1',
            'zobraz2': 'Zobraziť',
        }
        async with self._session.post('https://is.stuba.sk/auth/katalog/rozvrhy_view.pl', data=data) as response:
            with open(f'temp_images/{ais_id}_rozvrh.pdf', 'wb') as f:
                f.write(await response.read())
            return f'temp_images/{ais_id}_rozvrh.pdf'
