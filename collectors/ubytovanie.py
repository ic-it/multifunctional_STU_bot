import asyncio
import pay_by_square

from .parser.base import BaseParser
from dataclasses import dataclass, field
from lxml import etree



@dataclass
class UbyUserResidence:
    dormitory: str
    block: str
    floor: int
    cell: int
    room: int
    cost: float

    def __str__(self):
        return f"{self.dormitory} {self.block} {self.floor}{self.cell}/{self.room} {self.cost}€"

@dataclass
class UbyUserPayment:
    iban: str
    swift: str
    variable_symbol: str
    arrears: float
    scan_to_pay_code: str

@dataclass
class UbyUser:
    residence: UbyUserResidence
    payment: UbyUserPayment


class UbytovanieParser(BaseParser):
    def __init__(self, loop: asyncio.AbstractEventLoop, login: str = None, password: str = None) -> None:
        super().__init__(loop)
        self._login: str = login
        self._password: str = password
    
    async def login(self) -> None:
        cookies = {
            '_ga': 'GA1.2.798688000.1658932723'
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Origin': 'https://ubytovanie.stuba.sk',
            'Referer': 'https://ubytovanie.stuba.sk/',
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
            'login__username': self._login,
            'login__password': self._password,
            'login__acad_year_id': '14',
            'login__operate': 'Prihlásiť',
            'login__searchText': '',
        }

        async with self._session.post('https://ubytovanie.stuba.sk/', cookies=cookies, headers=headers, data=data):
            pass
    
    async def get_user(self) -> UbyUser:
        residence = await self.get_user_residence()
        payment = await self.get_user_payment()

        return UbyUser(
            residence=residence,
            payment=payment
        )

    async def get_user_residence(self) -> UbyUserResidence:
        async with self._session.get("https://ubytovanie.stuba.sk/?module=Reservation&submodule=reservation&mode=edit") as response:
            response_text = await response.text()
        
        dom = etree.HTML(response_text.encode('utf-8'))

        value = dom.xpath('//table[@class="evid_small"]')[0]
        residence = value.xpath('//tr[2]/td[1]/text()')[0].strip().split(' ')[::-1]

        dormitory = ' '.join(residence[2:][::-1])
        block = residence[1]
        
        if residence[0].isdigit():
            floor = int(residence[0][:2])
            cell = int(residence[0][2:])
            room = 0
        else:
            floor = int(residence[0].split('/')[0][:-1])
            cell  = int(residence[0].split('/')[0][-1:])
            room  = int(residence[0].split('/')[1])
        cost  = float(value.xpath('//tr[2]/td[3]/text()')[0].strip().replace('€', ''))

        return UbyUserResidence(
            dormitory=dormitory, 
            block=block, 
            floor=floor, 
            cell=cell, 
            room=room, 
            cost=cost)
        
    async def get_user_payment(self) -> UbyUserPayment:
        async with self._session.get("https://ubytovanie.stuba.sk/?module=Reservation&submodule=payment&template=payment") as response:
            response_text = await response.text()
        
        dom = etree.HTML(response_text)
        iban = dom.xpath('//form[@name="form"]/table/tr/td/table[1]/tr[3]/td/b/text()')[0].strip()
        swift = dom.xpath('//form[@name="form"]/table/tr/td/table[1]/tr[4]/td/b/text()')[0].strip()
        variable_symbol = dom.xpath('//form[@name="form"]/table/tr/td/table[1]/tr[6]/td[2]/b/span/text()')[0].strip()
        arrears = dom.xpath('//form[@name="form"]/table/tr/td/table[1]/tr[7]/td[2]/b/text()')[0].strip()

        iban = iban.split(': ', 1)[1]
        swift = swift.split(': ', 1)[1]
        arrears = float(''.join([c for c in arrears.replace(',', '.') if c.isdigit() or c == '.']))

        scan_to_pay_code = pay_by_square.generate(
            amount=arrears,
            iban=iban,
            swift=swift,
            variable_symbol=variable_symbol,
        )

        return UbyUserPayment(
            iban=iban,
            swift=swift,
            variable_symbol=variable_symbol,
            arrears=arrears,
            scan_to_pay_code=scan_to_pay_code)