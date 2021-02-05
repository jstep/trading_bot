# from bottrade import BotTrade
# from botindicators import BotIndicators
# from strategy.botstrategy import BotStrategy
#
#
# class MACDStrategyBasic(BotStrategy):
#     """
#     Basic MACD Strategy.
#     """
#     _NAME = 'MACD strategy basic'
#
#     # Entry strategy flags. Keep at least one set to true or the trade will never enter.
#
#     # Exit strategy flags. Keep at least one set to true or the trade will never exit.
#     TAKE_PROFIT = True
#     take_profit = 0.005
#     CROSSOVER = False
#
#     def __init__(self, pair, period):
#         BotStrategy.__init__(self, pair, period)
#
#         self.currentPrice = ""
#         self.pair = pair
#         self.macd_stop_loss = 0.25
#         self.max_hist = 0  # Used to keep track of the maximum value of the indicator used on this trade.

#
#         self.indicators = BotIndicators()
#
#         self.macd_fast = 12
#         self.macd_slow = 26
#         self.macd_signal = 9
#         self.macd_period = self.macd_signal + self.macd_slow  # Number of data points needed to use MACD indicator
#
#         self.past_avg_prices, _, _, _, _ = self.get_past_prices(self.period, self.macd_period)
#         if self.past_avg_prices:
#             self.prices = self.past_avg_prices
#
#     def tick(self, candlestick):
#         self.currentPrice = float(candlestick.typical_price)
#         self.prices.append(self.currentPrice)
#
#         if len(self.prices) > self.macd_period:
#             m, s, h = self.indicators.MACD(self.prices, self.macd_slow, self.macd_fast, self.macd_signal)
#             self.output.log("Price: " + str(candlestick.typical_price) + "\tMACD: " +
#                         str(m[-2:]) + "\tSignal: " + str(s[-2:]) + "\tHistogram: " + str(h[-2:]))
#
#         self.evaluate_positions()
#         self.update_open_trades()
#         self.show_positions()
#
#     def evaluate_positions(self):
#         openTrades = []
#         for trade in self.trades:
#             if trade.status == "OPEN":
#                 openTrades.append(trade)
#
#         # Instantiate indicator.
#         macd, signal, hist = self.indicators.MACD(self.prices, self.macd_slow, self.macd_fast, self.macd_signal)
#
#         # Only open a trade when the number of open trades is not more than the configured max allowed.
#         # And there is enough data for indicator
#         if len(openTrades) < self.num_simultaneous_trades and len(self.prices) > self.macd_period:
#             #########################
#             # Entry Strategy
#             #########################
#             # Buy/Long
#             # If second to last histogram is negative and last histogram value positive is its a crossover.
#             if hist[-2] < 0.0 < hist[-1]:
#                 self.output.log("{} buy signal".format(self._NAME))
#                 self.trades.append(BotTrade(self.pair, self.currentPrice, "BUY", stop_loss_percent=self.macd_stop_loss))
#
#             # NOTE: LEVERAGE REQUIRED FOR SELLING ON KRAKEN
#
#         ###############
#         # Exit Strategy
#         ###############
#         for trade in openTrades:
#             # Buy/Long Exit Strategy
#
#             if self.TAKE_PROFIT:
#                 # Exit on % profit.
#                 if self.currentPrice >= (trade.entry_price * (1.0 + self.take_profit)) and trade.trade_type.upper() == "BUY":
#                     self.output.log("{} Closed on {}% gain".format(self._NAME, self.take_profit * 100))
#                     trade.close(self.currentPrice)
#                     continue
#             if self.CROSSOVER:
#                 # Exit on cross over signal.
#                 if hist[-1] < 0.0 and trade.trade_type.upper() == "BUY":
#                     self.output.log("{} Closed on cross over".format(self._NAME))
#                     trade.close(self.currentPrice)
#                     continue
#
#             # TODO
#             # Sell/Short Exit Strategy  LEVERAGE REQUIRED FOR SHORTING ON KRAKEN
