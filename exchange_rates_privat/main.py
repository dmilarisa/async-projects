import json

import aiohttp
import asyncio
from datetime import datetime, timedelta
import platform
import sys


class HttpError (Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f"Connection error: {url}", str(err))


def day_currency(response):
    day = response['date']
    saleEUR,  purchaseEUR, saleUSD, purchaseUSD = None, None, None, None
    for el in response['exchangeRate']:
        if el['currency'] == "EUR":
            saleEUR = el['saleRate']
            purchaseEUR = el['purchaseRate']
        if el['currency'] == "USD":
            saleUSD = el['saleRate']
            purchaseUSD = el['purchaseRate']
    return {day:
                {'EUR': {'sale': saleEUR, 'purchase': purchaseEUR},
                 'USD': {'sale': saleUSD, 'purchase': purchaseUSD}}
            }


async def main(index_day):
    result = []
    for day in range(int(index_day)):
        shift = datetime.now() - timedelta(days=day)
        d = shift.strftime("%d.%m.%Y")
        try:
            response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={d}')
            result.append(day_currency(response))
        except HttpError as err:
            print(err)
            return None
    return result

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main(sys.argv[1]))
    print(json.dumps(r, indent=4))




