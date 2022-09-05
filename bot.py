import asyncio
import logging
import config

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.middlewares import BaseMiddleware


from collectors import AisParser, UbytovanieParser
from qrcode_styled import QRCodeStyled
from antiflood import ThrottlingMiddleware, rate_limit



logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.BOT_API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class LoginForm(StatesGroup):
    login = State()
    password = State()

class BotStates(StatesGroup):
    home = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await LoginForm.login.set()

    await message.answer(config.HELLO_MESSAGE)
    await message.answer("First, I have to get the login information for AIS/Ubytovanie.")
    await message.answer("Enter your login:")



@dp.message_handler(state=LoginForm.login)
async def get_user_login(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['login'] = message.text

    await LoginForm.next()
    await message.answer("Enter your password:")


@dp.message_handler(state=LoginForm.password)
async def get_user_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text

        async with AisParser(asyncio.get_event_loop(), data['login'], data['password']) as parser:
            if not await parser.login():
                await message.answer("Login unsuccessful!")
                await message.answer("Enter your login:")
                await state.finish()
                await LoginForm.login.set()
                await message.delete()
                return
            
            await dp.storage.set_data(user=message.from_user.id, data={
                'login': data['login'],
                'password': data['password']
            })
            await message.answer("Login successful!")
            await message.answer("/getdata - get data from Ubytovanie")
            await state.finish()
            await BotStates.home.set()
            await message.delete()
            return


@dp.message_handler(state=BotStates.home)
@rate_limit(2, 'BotStates.home')
async def get_user_password(message: types.Message, state: FSMContext):    
    await message.answer("Wait a minute. Loading data...")
    user_data = await dp.storage.get_data(user=message.from_user.id)

    async with UbytovanieParser(asyncio.get_event_loop(), user_data.get("login"), user_data.get("password")) as parser:
        await parser.login()
        uby_user = await parser.get_user()
    
    await message.answer("Ubytovanie menu:")
    msg = f"{uby_user.residence}\n" \
            f"iban: {uby_user.payment.iban}\n"\
            f"variable_symbol: {uby_user.payment.variable_symbol}\n"\
            f"arrears: {uby_user.payment.arrears}\n"
    
    await message.answer(msg)

    qr = QRCodeStyled()

    with open(f'./temp_images/{message.from_user.id}.png', 'wb') as _fh:
        qr.get_image(uby_user.payment.scan_to_pay_code).save(_fh, 'PNG', lossless=False, quaility=250, method=2)
    
    await message.answer_photo(photo=open(f'./temp_images/{message.from_user.id}.png', 'rb'), caption="Scan to pay")


class LogMiddleware(BaseMiddleware):
    def __init__(self):
        super(LogMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        state = await data.get('state').get_state() if data.get('state') else None
        if state and state.startswith('LoginForm'):
            print(f"Message[{message.from_user.id}][@{message.from_user.username}][{message.from_user.full_name}][{state}]: {'*'*len(message.text)}")
            return
        print(f"Message[{message.from_user.id}][@{message.from_user.username}][{message.from_user.full_name}][{state}]: {message.text}")

if __name__ == '__main__':
    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(LogMiddleware())


    executor.start_polling(dp, skip_updates=True)