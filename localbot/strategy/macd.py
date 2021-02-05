from datadog import statsd

from bottrade import BotTrade
from botindicators import BotIndicators
from strategy.botstrategy import BotStrategy

from colours import *
from constants import BOT_ID, BOT_NAME


class MACDStrategy(BotStrategy):
    """
    New MACD strategy

    """
    _NAME = 'MACD Strategy'


    # Entry strategy flags. Keep at least one set to true or the trade will never enter
    MACD_CROSSOVER = True

    # Exit strategy flags. Keep at least one set to true or the trade will never exit
    TAKE_PROFIT = True
    take_profit = 0.007  # Exit when realized profit of trade is above this percentage. e.g. 0.005 == 0.5%

    def __init__(self, pair, period):
        BotStrategy.__init__(self, pair, period)

        self.highs = []
        self.lows = []
        self.closes = []
        self.current_price = ""
        self.pair = pair
        self.stop_loss_percent = 2.5

        self.indicators = BotIndicators()

        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.macd_period = self.macd_signal + self.macd_slow  # Number of data points needed to use MACD indicator
        self.hist_period = max(self.macd_fast, self.macd_slow, self.macd_signal, self.macd_period)
        self.max_hist = 0  # Used to keep track of the maximum value of the MACD histogram used on this trade.

        # Prime the bot with past data.
        self.past_typical_prices, self.past_opens, self.past_closes, self.past_highs, self.past_lows = self.get_past_prices(self.period, self.hist_period)
        if self.past_typical_prices and self.past_closes and self.past_highs and self.past_lows and self.past_opens:
            self.prices = self.past_typical_prices
            self.closes = self.past_closes
            self.highs = self.past_highs
            self.lows = self.past_lows

    def tick(self, candlestick):

        self.current_price = float(candlestick.typical_price)
        self.prices.append(self.current_price)

        # Highs
        self.currentHigh = float(candlestick.high)
        self.highs.append(self.currentHigh)

        # Lows
        self.currentLow = float(candlestick.low)
        self.lows.append(self.currentLow)

        # Closes
        self.currentClose = float(candlestick.close)
        self.closes.append(self.currentClose)

        if len(self.prices) > self.hist_period:
            # Price action
            self.output.log("\n{color}Typical Price: {price}".format(color=Cyan, price=str(candlestick.typical_price)))

            # MACD
            m, s, h = self.indicators.MACD(self.prices, self.macd_slow, self.macd_fast, self.macd_signal)
            self.output.log("Last/Current indicator values:\tMACD {}\tSignal: {}\t Hist: {}".format(str(m[-2:]), str(s[-2:]), str(h[-2:])))

            statsd.histogram('macd.macd', m[-1], tags=['macd.macd_line', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
            statsd.histogram('macd.signal', s[-1], tags=['macd.signal_line', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
            statsd.histogram('macd.histogram', h[-1], tags=['macd.histogram', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

            self.output.log(White)

        self.evaluate_positions()
        self.update_open_trades()
        self.show_positions()

    def evaluate_positions(self):
        openTrades = []
        for trade in self.trades:
            if trade.status == "OPEN":
                openTrades.append(trade)

        # Instantiate indicator.
        _, _, hist = self.indicators.MACD(self.prices, self.macd_slow, self.macd_fast, self.macd_signal)

        # Only open a trade when the number of open trades is not more than the configured max allowed.
        # And there is enough data for indicator
        if len(openTrades) < self.num_simultaneous_trades and len(self.prices) > self.hist_period:
            #########################
            # Entry Strategy
            #########################
            # Buy/Long
            if self.MACD_CROSSOVER:
                if hist[-2] < 0.0 < hist[-1]:
                    self.output.log("{} buy signal. MACD crossover".format(self._NAME))
                    self.trades.append(BotTrade(pair=self.pair, current_price=self.current_price, trade_type="BUY", order_type='market',  stop_loss_percent=self.stop_loss_percent))

            # NOTE: LEVERAGE REQUIRED FOR SELLING ON KRAKEN
        ###############
        # Exit Strategy
        ###############
        for trade in openTrades:
            # Buy/Long
            if self.TAKE_PROFIT:
                # Exit on % profit.
                if self.current_price >= (trade.entry_price * (1.0 + self.take_profit)) and trade.trade_type.upper() == "BUY":
                    self.output.log("{} Closed on {}% gain".format(self._NAME, self.take_profit * 100))
                    trade.close(self.current_price)
                    continue

            # TODO
            # Sell/Short Exit Strategy  LEVERAGE REQUIRED FOR SHORTING ON KRAKEN
