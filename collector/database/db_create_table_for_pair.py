import os
import sys
from psycopg2.pool import SimpleConnectionPool

# Allows import from parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from exchanges.krakenex.public import AssetPairs


dbConnection = "dbname='kraken' user='James' host='localhost' password=''"


def create_table_for_pair(pair):
    pool = SimpleConnectionPool(1, 10, dbConnection)
    client = pool.getconn()
    cursor = client.cursor()
    try:
        query = """CREATE TABLE IF NOT EXISTS orderbook_{pair}
        (
            id SERIAL PRIMARY KEY NOT NULL,
            seq INTEGER NOT NULL,
            is_bid BOOLEAN,
            price DOUBLE PRECISION,
            size DOUBLE PRECISION,
            ts DOUBLE PRECISION,
            trade_id VARCHAR(32),
            type INTEGER
        );
        CREATE UNIQUE INDEX IF NOT EXISTS
          orderbook_{pair}_id_uindex ON orderbook_{pair} (id);

        CREATE TABLE IF NOT EXISTS orderbook_snapshot_{pair}
        (
            id SERIAL PRIMARY KEY NOT NULL,
            seq INTEGER NOT NULL,
            snapshot JSON NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS
          orderbook_snapshot_{pair}_id_uindex ON orderbook_snapshot_{pair} (id);"""

        query = query.format(pair=pair)
        print("Executing...")
        print(query)
        cursor.execute(query)
        client.commit()
    finally:
        client.close()

    return True


def get_all_market_pairs():
    # Get a list of all asset pairs from Kraken.
    # [u'XXBTZCAD',
    # u'XXMRZUSD',
    # u'XXBTZEUR.d',
    # u'EOSUSD',
    # ...]

    try:
        asset_pairs = AssetPairs().get('result').keys()
        # Kraken designates dark pool with `.d` on the asset pair.
        # The Kraken dark pool is an order book not visible to the rest of the market.
        # Each trader only knows their own orders. So, there is no benefit to storing
        # these order books and we exclude assets ending in `.d`.
        return [x for x in asset_pairs if not x.endswith('.d')]
    except:
        print("AssetPairs API call failed. Re-run script")


def init_tables_for_all_assets():
    """
    Create order book and order book snapshot tables for all pairs in an exchange.
    """
    markets = get_all_market_pairs()

    for pair in markets:
        create_table_for_pair(pair)
        print("Created order book tables for {} pair".format(pair))
