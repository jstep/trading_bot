# -*- coding: utf-8 -*-

import asyncio
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt.async as ccxt

exchange = ccxt.kraken()


async def poll():
    while True:
        yield await exchange.fetch_order_book('BTC/USD')
        await asyncio.sleep(exchange.rateLimit / 1000)


async def main():
    async for orderbook in poll():
        print(orderbook['bids'][0], orderbook['asks'][0], orderbook['timestamp'])


asyncio.get_event_loop().run_until_complete(main())