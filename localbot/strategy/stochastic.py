from bottrade import BotTrade
from botindicators import BotIndicators
from strategy.botstrategy import BotStrategy


class StochasticStrategyBasic(BotStrategy):
    """
    Basic Stochastic Oscillator Strategy.
    """
    _NAME = 'Stochastic strategy basic'

    # Entry strategy flags. Keep at least one set to true or the trade will never enter.

    # Exit strategy flags. Keep at least one set to true or the trade will never exit.
    TAKE_PROFIT = True
    take_profit = 0.004

    OVER_BOUGHT = True

    def __init__(self, pair, period):
        BotStrategy.__init__(self, pair, period)

        self.highs = []
        self.lows = []
        self.closes = []
        self.currentPrice = ""
        self.pair = pair
        self.stoch_stop_loss = 100.0

        self.indicators = BotIndicators()

        self.stoch_period = 14  # n previous trading sessions (candles)
        self.over_bought = 80
        self.over_sold = 20

        self.past_avg_prices, self.past_opens, self.past_closes, self.past_highs, self.past_lows = self.get_past_prices(self.period, self.stoch_period)
        if self.past_avg_prices and self.past_closes and self.past_highs and self.past_lows and self.past_opens:
            self.prices = self.past_avg_prices
            self.closes = self.past_closes
            self.highs = self.past_highs
            self.lows = self.past_lows

    def tick(self, candlestick):
        self.currentPrice = float(candlestick.typical_price)
        self.prices.append(self.currentPrice)

        # Highs
        self.currentHigh = float(candlestick.high)
        self.highs.append(self.currentHigh)

        # Lows
        self.currentLow = float(candlestick.low)
        self.lows.append(self.currentLow)

        # Closes
        self.currentLow = float(candlestick.close)
        self.closes.append(self.currentLow)

        if len(self.prices) > self.stoch_period:
            k, d = self.indicators.STOCH(self.highs, self.lows, self.closes)
            self.output.log("Price: " + str(candlestick.typical_price) + "\t%K: " + str(k[-1:]) + "\t%D: " + str(d[-1:]))

        self.evaluate_positions()
        self.update_open_trades()
        self.show_positions()

    def evaluate_positions(self):
        openTrades = []
        for trade in self.trades:
            if trade.status == "OPEN":
                openTrades.append(trade)

        # Instantiate indicator.
        slowk, slowd = self.indicators.STOCH(self.highs, self.lows, self.closes)

        # Only open a trade when the number of open trades is not more than the configured max allowed.
        # And there is enough data for indicator
        if len(openTrades) < self.num_simultaneous_trades and len(self.prices) > self.stoch_period:
            #########################
            # Entry Strategy
            #########################
            # Buy/Long
            if slowk[-1] <= self.over_sold:
                self.output.log("{} buy signal".format(self._NAME))
                self.trades.append(BotTrade(pair=self.pair, current_price=self.currentPrice, trade_type="BUY", order_type='market',  stop_loss_percent=self.stoch_stop_loss))
            # NOTE: LEVERAGE REQUIRED FOR SELLING ON KRAKEN
        ###############
        # Exit Strategy
        ###############
        for trade in openTrades:
            # Buy/Long

            if self.TAKE_PROFIT:
                # Exit on % profit.
                if self.currentPrice >= (trade.entry_price * (1.0 + self.take_profit)) and trade.trade_type.upper() == "BUY":
                    self.output.log("{} Closed on {}% gain".format(self._NAME, self.take_profit * 100))
                    trade.close(self.currentPrice)
                    continue
            if self.OVER_BOUGHT:
                # Exit on overbought signal.
                if slowk[-1] >= self.over_bought and trade.trade_type.upper() == "BUY":
                    self.output.log("{} Closed on over bought signal".format(self._NAME))
                    trade.close(self.currentPrice)
                    continue

            # TODO
            # Sell/Short Exit Strategy  LEVERAGE REQUIRED FOR SHORTING ON KRAKEN