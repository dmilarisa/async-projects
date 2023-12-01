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


def day_currency(response, currencies):
    day = response['date']
    day_data = {day: {}}
    for currency in currencies:
        for el in response['exchangeRate']:
            if el['currency'] == currency:
                rates = {"sale": el["saleRateNB"], "purchase": el["purchaseRateNB"]}
                day_data[day].update({currency: rates})
    return day_data


async def main(input_data):
    index_day = input_data[0]
    currencies = ['EUR', 'USD']
    if len(input_data) == 2:
        currencies.append(input_data[1])
    result = []
    for day in range(int(index_day)):
        shift = datetime.now() - timedelta(days=day)
        d = shift.strftime("%d.%m.%Y")
        try:
            response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={d}')
            result.append(day_currency(response, currencies))
        except HttpError as err:
            print(err)
            return None
    return result

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main(sys.argv[1:]))
    print(json.dumps(r, indent=4))






