import asyncio
import logging

import aiohttp
from datetime import datetime, timedelta
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


async def request(url: str) -> dict | str:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    return "Status error"
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            return "Connection error"


async def get_exchange():
    day = datetime.now().strftime("%d.%m.%Y")
    day_data = {day: {}}
    response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={day}')
    currencies = ('USD', 'EUR')
    for currency in currencies:
        for el in response['exchangeRate']:
            if el['currency'] == currency:
                rates = {"sale": el["saleRateNB"], "purchase": el["purchaseRateNB"]}
                day_data[day].update({currency: rates})
    return day_data


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                exchange = await get_exchange()
                await self.send_to_clients(str(exchange))
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())