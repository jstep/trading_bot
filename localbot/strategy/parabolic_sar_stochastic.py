from datadog import statsd

from bottrade import BotTrade
from botindicators import BotIndicators
from strategy.botstrategy import BotStrategy

from colours import *
from constants import BOT_ID, BOT_NAME


class ParabolicSARStochasticStrategySR(BotStrategy):
    """
    Stochastic Oscillator Strategy with Parabolic SAR confirmation.
    Includes flags to control entry/exit based on various moving average cases.

    """
    _NAME = 'Parabolic SAR/Stochastic Crossover Strategy'


    # Entry strategy flags. Keep at least one set to true or the trade will never enter
    PRICE_ABOVE_MA = False
    STOCH_OS = False
    SAR_STOCH = True

    # Exit strategy flags. Keep at least one set to true or the trade will never exit
    TAKE_PROFIT = True
    take_profit = 0.005  # Exit when realized profit of trade is above this percentage. e.g. 0.005 == 0.5%
    MA_SLOPE_SLOWING = True  # Exit when moving average slope begins to decline
    PRICE_BELOW_MA = False  # Exit when price is below moving average

    def __init__(self, pair, period):
        BotStrategy.__init__(self, pair, period)

        self.highs = []
        self.lows = []
        self.closes = []
        self.moving_avgs = []  # Keep track of MAs
        self.ma_slopes = []  # Keep track of Slope of MAs
        self.slope_difference = []
        self.current_price = ""
        self.pair = pair
        self.stoch_stop_loss = 2.5
        self.cool_down_period = 0

        self.indicators = BotIndicators()

        # Lookback window sizes
        self.stoch_period = 5  # n previous candles for stochastic indicator
        self.ma_period_fast = 9  # n previous candles for fast moving average indicator
        self.ma_slope_lookback = 9  # n previous values for calculating slope of MA.
        self.ma_period_slow = 26  # n previous candles for slow moving average indicator
        self.sr_n = 25  # n-value for S/R indicator. Controls Smoothing.
        self.hist_period = max(self.stoch_period, self.ma_period_fast, self.ma_period_slow)

        self.over_bought = 80
        self.over_sold = 20
        self.mid_line = 50
        self.ready_to_buy = False

        # Prime the bot with past data.
        self.past_typical_prices, self.past_opens, self.past_closes, self.past_highs, self.past_lows = self.get_past_prices(self.period, self.hist_period)
        if self.past_typical_prices and self.past_closes and self.past_highs and self.past_lows and self.past_opens:
            self.prices = self.past_typical_prices
            self.closes = self.past_closes
            self.highs = self.past_highs
            self.lows = self.past_lows
        for i in reversed(range(self.ma_period_fast)):
            sub_slice = self.prices[:-i - 1]
            _ma = self.indicators.moving_average(sub_slice[-self.ma_period_fast:], self.ma_period_fast)
            self.moving_avgs.append(_ma)

    def tick(self, candlestick):
        if self.cool_down_period:
            self.cool_down_period -= 1
        # self.output.log("cool down: {}".format(self.cool_down_period))

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
            self.output.log("\n{color}Typical Price: {price}".format(color=Red, price=str(candlestick.typical_price)))

            # Moving average
            m_a = self.indicators.moving_average(self.closes, self.ma_period_fast)
            self.moving_avgs.append(m_a)
            self.output.log("Current Moving Average Value: " + str(m_a))
            # self.output.log("Last {} Moving Average Values: {}".format(self.ma_period_fast, str(self.moving_avgs[-self.ma_period_fast:])))
            statsd.histogram('stochastic.moving_average', m_a, tags=['stochastic.moving_average', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

            # Slope of moving averages trend line
            slope = self.indicators.slope(self.moving_avgs, lookback=self.ma_slope_lookback)
            self.ma_slopes.append(slope)
            self.output.log("Slope over last {} periods: {}".format(str(self.ma_slope_lookback), str(self.ma_slopes[-1])))
            # self.output.log("Slope values: {}".format(str(self.ma_slopes)))
            # Create a new list of change in value between values in an old list. e.g. [1,1,2,3,5,8] == [0, 1, 1, 2, 3]
            # Simple approximation for rate of change.
            self.slope_difference = [j-i for i, j in zip(self.ma_slopes[:-1], self.ma_slopes[1:])]
            # self.output.log("Slope differences: {}".format(self.slope_difference))
            statsd.histogram('stochastic.slope', slope, tags=['stochastic.slope', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

            # Trend direction
            trend_dir = self.price_to_ma_trend(candlestick.typical_price, m_a)
            self.output.log("Price to MA trend direction: {} (price to moving average) ".format(str(trend_dir)))
            statsd.histogram('stochastic.trend', trend_dir, tags=['stochastic.trend', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

            # Stochastic
            k, d = self.indicators.STOCH(self.highs, self.lows, self.closes, fastk_period=self.stoch_period)
            self.output.log("\n{color}%K: {k}\t%D: {d}".format(color=Yellow, k=str(k[-1:]), d=str(d[-1:])))

            # Stochastic Ready to Buy - True
            if (k[-1] < self.mid_line and d[-1] < self.mid_line) and k[-2] < d[-2] and k[-1] > d[-1]:
                self.ready_to_buy = True
            # Stochastic Ready to Buy - False
            if (k[-1] > self.mid_line and d[-1] > self.mid_line) and k[-2] > d[-2] and k[-1] < d[-1]:
                self.ready_to_buy = False
            self.output.log("Stochastic ready to buy: {}".format(self.ready_to_buy))

            statsd.histogram('stochastic.percent_k', k[-1], tags=['stochastic.percent_k', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
            statsd.histogram('stochastic.percent_d', d[-1], tags=['stochastic.percent_d', 'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        self.evaluate_positions()
        self.update_open_trades()
        self.show_positions()

    def evaluate_positions(self):
        openTrades = []
        for trade in self.trades:
            if trade.status == "OPEN":
                openTrades.append(trade)

        # Instantiate indicator.
        slowk, slowd = self.indicators.STOCH(self.highs, self.lows, self.closes, fastk_period=self.stoch_period)
        sar = self.indicators.SAR(self.highs, self.lows)

        # Only open a trade when the number of open trades is not more than the configured max allowed.
        # And there is enough data for indicator
        if len(openTrades) < self.num_simultaneous_trades and len(self.prices) > self.hist_period:
            #########################
            # Entry Strategy
            #########################
            # Buy/Long
            if self.PRICE_ABOVE_MA:
                if self.moving_avgs[-1] < self.current_price and self.ready_to_buy and not self.cool_down_period:
                    self.output.log("{} buy signal. Ready to buy: {} & typical price {} above MA".format(self._NAME,
                                                                                                         self.ready_to_buy,
                                                                                                         self.current_price - self.moving_avgs[-1]))
                    self.trades.append(BotTrade(pair=self.pair, current_price=self.current_price, trade_type="BUY", order_type='market',  stop_loss_percent=self.stoch_stop_loss))
                    self.cool_down_period = 5  # Wait n periods until another trade can be made
            if self.STOCH_OS:
                # Stochastic %K crossover %D below midline (50)
                if slowk[-1] < self.mid_line and slowd[-1] < self.mid_line and slowk[-2] < slowd[-2] and slowk[-1] > slowd[-1]:
                    self.output.log("{} buy signal. Stochastic %K crossover %D below midline(50)".format(self._NAME,
                                                                                                         self.ready_to_buy,
                                                                                                         self.current_price - self.moving_avgs[-1]))
                    self.trades.append(BotTrade(pair=self.pair, current_price=self.current_price, trade_type="BUY", order_type='market',  stop_loss_percent=self.stoch_stop_loss))
            if self.SAR_STOCH:
                # Stochastic %K crossover %D below midline (50) and SAR is less than current price
                if self.ready_to_buy and sar[-1] < self.current_price:
                    self.output.log("{} buy signal. Stochastic ready to buy & SAR below current price)".format(self._NAME,
                                                                                                               self.ready_to_buy,
                                                                                                               self.current_price - self.moving_avgs[-1]))
                    self.trades.append(BotTrade(pair=self.pair, current_price=self.current_price, trade_type="BUY", order_type='market',  stop_loss_percent=self.stoch_stop_loss))


            # NOTE: LEVERAGE REQUIRED FOR SELLING ON KRAKEN
        ###############
        # Exit Strategy
        ###############
        for trade in openTrades:
            # Buy/Long
            if self.MA_SLOPE_SLOWING and len(self.slope_difference) > 6:
                # Exit when the rate of the SLOPE of the n-period MA begins to slow.
                if self.slope_difference[-1] < self.slope_difference[-2] < self.slope_difference[-3] < \
                        self.slope_difference[-4] < self.slope_difference[-5] < self.slope_difference[-6] < \
                        self.slope_difference[-7] < self.slope_difference[-8]:
                    self.output.log("{} Closed on slope slowing. Slope went down by {}, {}, {}, {}".format(
                        self._NAME,
                        self.slope_difference[-4],
                        self.slope_difference[-3],
                        self.slope_difference[-2],
                        self.slope_difference[-1]))
                    trade.close(self.current_price)
                    continue
            if self.TAKE_PROFIT:
                # Exit on % profit.
                if self.current_price >= (trade.entry_price * (1.0 + self.take_profit)) and trade.trade_type.upper() == "BUY":
                    self.output.log("{} Closed on {}% gain".format(self._NAME, self.take_profit * 100))
                    trade.close(self.current_price)
                    continue

            # TODO
            # Sell/Short Exit Strategy  LEVERAGE REQUIRED FOR SHORTING ON KRAKEN

    @staticmethod
    def price_to_ma_trend(price, moving_avg):
        if price <= moving_avg:
            trend = "DOWN"
        elif price > moving_avg:
            trend = "UP"
        else:
            trend = "NEUTRAL"
        return trend
