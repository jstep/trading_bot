# -*- coding: utf-8 -*-

import asyncio
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt.async as ccxt

exchange = ccxt.kraken()

store = []

async def poll_recent_trades():
    while True:
        yield await exchange.fetch_trades(symbol='BTC/USD')
        await asyncio.sleep(exchange.rateLimit / 1000)

async def poll():
    while True:
        yield await exchange.fetch_order_book(symbol='BTC/USD', limit=100, params={'timestamp': 1})
        await asyncio.sleep(exchange.rateLimit / 1000)


# NOTES:
# Kraken order book can be up to 1000 entries long (500 bid, 500 asks).
# Even at the minimum poll time it is possible that the order book does not change
# between pollings. When storing into a DB, only store the changes.

async def main():
    # async for orderbook in poll():
        # print(orderbook)
    async for trades in poll_recent_trades():
        print(trades)
        # print(orderbook['timestamp'], orderbook['datetime'])
        # bids = orderbook['bids'][0]
        # asks = orderbook['asks'][0]
        # ts = orderbook.get('timestamp')
        # print(ts)
        # store.append(bids + asks)
        #
        # if len(store) > 2:
        #     if store[-2] == store[-1]:
        #         print("\033[46m"+'they were the same'+"\033[40m")
        #         print(store[-1])
        #     else:
        #         print('they were different')
        #         print(store[-1])



asyncio.get_event_loop().run_until_complete(main())
