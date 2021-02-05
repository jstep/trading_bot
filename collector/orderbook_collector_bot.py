import asyncio
import os
import sys
import json
from psycopg2.pool import SimpleConnectionPool

# Allows import from parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from exchanges.krakenex_py3.public import Depth

dbConnection = "dbname='kraken' user='James' host='localhost' password=''"

pair = 'XXBTZUSD'
depth_count = 4
rate_limit = 3000  # milliseconds
store = []

async def poll():
    while True:
        # yield await exchange.fetch_order_book(symbol='BTC/USD', limit=100)
        yield Depth(pair=pair, count=depth_count)
        await asyncio.sleep(rate_limit / 1000)


# NOTES:
# Kraken order book can be up to 1000 entries long (500 bid, 500 asks).
# Even at the minimum poll time it is possible that the order book does not change
# between pollings. When storing into a DB, only store the changes.

async def main():
    pool = SimpleConnectionPool(1, 10, dbConnection)
    conn = pool.getconn()
    cursor = conn.cursor()

    async for orderbook in poll():
        try:
            orderbook_pair = orderbook.get('result', {}).get(pair, {})
            for item in orderbook_pair['bids']:
                print(item)
            print()
            for item in orderbook_pair['asks']:
                    print(item)
        finally:
            conn.close()

asyncio.get_event_loop().run_until_complete(main())
