import sys
import os
import logging


from botlog import BotLog

# Allows import from parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from exchanges.krakenex.public import OHLC

logger = logging.getLogger()


class BotStrategy(object):
    """
    This is the base Strategy object.
    Any new strategies must extend from this class to inherit key functionality.
    """
    _NAME = NotImplemented

    def __init__(self, pair, period):
        self.output = BotLog()
        self.prices = []
        self.trades = []
        self.current_price = NotImplemented

        self.period = period

        self.num_simultaneous_trades = 3  # Max number of simultaneous trades

    @classmethod
    def get_name(cls):
        return cls._NAME

    def tick(self, candlestick):
        raise NotImplementedError

    def evaluate_positions(self):
        raise NotImplementedError

    def update_open_trades(self):
        for trade in self.trades:
            if trade.status == "OPEN":
                trade.tick(self.current_price)

    def show_positions(self):
        for trade in self.trades:
            trade.show_trade()

    def get_past_prices(self, candle_width, lookback):
        """Get past close prices
         :param candle_width Candlestick width in minutes, [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
         :param lookback How many past candlesticks to get.
         """
        logger.info("Fetching historical OHLC data for technical indicators...")
        ohlc = OHLC(pair='XXBTZUSD', interval=candle_width)
        if not ohlc['error']:
            past_data = ohlc['result'][self.pair][-lookback:]
        else:
            self.output.log(ohlc['error'])
            return

        # Make a list of past prices.
        past_typical_prices = []  # Arithmetic averages of the high, low, and closing prices for a given period.
        past_open_prices = []
        past_close_prices = []
        past_high_prices = []
        past_low_prices = []
        for data in past_data:
            typical_price = (float(data[2]) + float(data[3]) + float(data[4])) / 3
            past_typical_prices.append(typical_price)
            past_open_prices.append(float(data[1]))
            past_close_prices.append(float(data[4]))
            past_high_prices.append(float(data[2]))
            past_low_prices.append(float(data[3]))
        return past_typical_prices, past_open_prices, past_close_prices, past_high_prices, past_low_prices

