import logging
import time
import sys
import os

from botcandlestick import BotCandlestick
from botlog import BotLog

# Allows import from parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from exchanges.krakenex.public import OHLC, Ticker


SECONDS_IN_DAY = 60 * 60 * 24

logger = logging.getLogger()


class BotChart(object):
    def __init__(self, exchange, pair, period, backtest=True):  # TODO: pass in start and end timestamps for backtesting
        self.output = BotLog()
        self.exchange = exchange
        self.pair = pair
        self.period = period
        self.startTime = time.time() - SECONDS_IN_DAY * 2  # TODO: use passed in start and end timestamps
        self.endTime = time.time()  # Backtest up to now TODO: move this to __init__ param so it can be changed

        self.data = []
        
        if self.exchange == "kraken" and backtest:
            logger.info("Fetching historical OHLC data for back testing...")
            kraken_data = OHLC(pair='XXBTZUSD', since=self.startTime, interval=self.period)
            historical_kraken_data = kraken_data['result'][self.pair]
            for datum in historical_kraken_data:
                if datum[1] and datum[4] and datum[2] and datum[3] and datum[5]:
                    # list entries: (0: <timestamp>, 1: <open>, 2: <high>, 3: <low>, 4: <close>, 5: <vwap>, 6: <volume>, 7: <count>)
                    self.data.append(BotCandlestick(self.period, datum[1], datum[4], datum[2], datum[3], datum[5]))

    def get_points(self):
        return self.data

    def get_current_price_and_vol(self):
        """"
        Get last price from ticker
        """
        current_values = Ticker()
        last_pair_price = current_values['result'][self.pair]['c'][0]
        last_pair_volume = current_values['result'][self.pair]['c'][1]

        # inside_bid = current_values['result'][self.pair]['b'][0]
        # inside_ask = current_values['result'][self.pair]['a'][0]
        return last_pair_price, last_pair_volume

    def get_ticker(self):
        """
        Get ticker info

        :return dict of ticker results or empty dict if error.
        """
        ticker = Ticker(pair=self.pair)
        if not ticker['error']:
            return ticker['result']
        else:
            self.output.log(ticker)
            return {}

    def midpoint_price(self):
        """
        The price between the best price of the sellers of the
        stock or commodity offer price or ask price and the best price
        of the buyers of the stock or commodity bid price. It can simply
        be defined as the average of the current bid and ask prices being quoted.
        AKA the "fair price".
        """
        ticker = Ticker()
        best_bid_price = ticker.get('result')[self.pair]['b'][0]
        best_ask_price = ticker.get('result')[self.pair]['a'][0]
        return (float(best_bid_price) + float(best_ask_price)) / 2

    def spread_percentage(self):
        """
        Bid-Ask spread as a percentage.
        """
        ticker = Ticker()
        b = ticker['result'][self.pair]['b'][0]
        a = ticker['result'][self.pair]['a'][0]
        return 100 * ((float(a) - float(b))/float(a))
