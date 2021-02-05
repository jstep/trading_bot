import time

from datadog import statsd

from botlog import BotLog
from constants import BOT_ID, BOT_NAME


class BotCandlestick(object):
    def __init__(self, period=None, open=None, close=None, high=None, low=None, typical_price=None):
        """"""
        self.output = BotLog()
        self.current = None
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.period = period
        self.startTime = time.time()
        self.typical_price = typical_price

    def tick(self, price, **kwargs):
        self.current = float(price)

        # If it's a brand new price the open price hasn't been set yet
        # then the current price is the open price.
        if self.open is None:
            self.open = self.current

        # If it's a brand new price the high price hasn't been set yet,
        # or if the current price is greater than the current high
        # then set this current price as the high.
        if (self.high is None) or (self.current > self.high):
            self.high = self.current

        # If it's a brand new price the low price hasn't been set yet,
        # or if the current price is less than the current low
        # then set this current price as the low.
        if (self.low is None) or (self.current < self.low):
            self.low = self.current

        # If the current time is at or after the start time plus the period
        # (i.e. this will be the last price that goes into this candlestick before
        # it is added to the list of past candlesticks) then set this current price
        # as the closing price.
        if time.time() >= (self.startTime + (self.period * 60)):
            self.close = self.current
            # Determine the typical price over entire period of the candlestick.
            self.typical_price = (self.high + self.low + self.close) / float(3)

        # Show OHLC data on each tick
        self.output.log(" Open: " + str(self.open) +
                        " Close: " + str(self.close) +
                        " High: " + str(self.high) +
                        " Low: " + str(self.low) +
                        " Current: " + str(self.current))

        statsd.histogram('candlestick.price.close', self.close, tags=['candlestick.price.close', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
        statsd.histogram('candlestick.price.high', self.high, tags=['candlestick.price.high', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
        statsd.histogram('candlestick.price.low', self.low, tags=['candlestick.price.low', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
        statsd.histogram('candlestick.price.typical_price', self.typical_price, tags=['candlestick.price.typical_price', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

    def isClosed(self):
        if self.close is not None:
            return True
        else:
            return False

