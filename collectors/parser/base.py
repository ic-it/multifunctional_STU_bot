from typing import TypeVar
import aiohttp
import asyncio


_T = TypeVar('_T', bound='BaseParser')

class BaseParser:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._session: aiohttp.ClientSession = None
        self._connections_limit: int = 5
        self._main_loop: asyncio.AbstractEventLoop = loop if loop else asyncio.get_event_loop()
    
    async def get_new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self._connections_limit)
        )

    async def get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = await self.get_new_session()

        return self._session
    
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._main_loop

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session
    
    @property
    def connections_limit(self) -> int:
        return self._connections_limit
    
    async def parse(self) -> None:
        """
        Here you can implement your logic to parse the page.
        """
        pass
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        
    async def __aenter__(self: _T) -> _T:
        """
        HAHAHAHAHAHAHHAHAAHHA. IT WORKS. I AM THE BEST.
        self: _T its GENIUS.
        """
        await self.get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()