import os
import sys
import json
import random
from datetime import datetime

from datadog import statsd

from botlog import BotLog
from colours import *
from constants import BOT_ID, BOT_NAME, VALIDATE
from utils.services import slack

# Allows import from parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from exchanges.krakenex.private import AddOrder, QueryOrders, QueryTrades, TradeVolume

if VALIDATE:
    print "{}PAPER TRADING - {}:{}{}".format(On_Cyan, BOT_ID, BOT_NAME, White)
else:
    print "{}LIVE TRADING - {}:{}{}".format(On_Cyan, BOT_ID, BOT_NAME, White)


class BotTrade(object):
    def __init__(self, pair, current_price, trade_type=None, order_type='market', stop_loss_percent=0):
        self.output = BotLog()
        self.pair = pair
        self.status = "OPEN"
        self.entry_price = 0.0
        self.exit_price = 0.0
        self.entry_cost = 0.0
        self.exit_cost = 0.0
        self.profit = 0.0
        self.fees = 0.0
        self.fee_percentage = 0.0
        self.exit_minus_entry_less_fees = 0.0
        self.trade_pl = None
        self.trade_net_precent = 0.0
        self.trade_type = trade_type  # BUY/SELL
        self.order_type = order_type  # Market/Limit/stop loss/settle position/etc.
        self.min_bid = 0.002
        self.open_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.close_time = "---------- --:--:--"
        self.stop_loss_percent = stop_loss_percent

        self.open_order_id = ""
        self.close_order_id = ""

        # user reference id.  32-bit signed number.
        # 1-bit for sign, 3-bits for 3 decimal digit (0-999), 8-bits for for randomly generated id.
        self.user_ref_id = int(str(BOT_ID) + str(int(random.getrandbits(7))))

        # self.usd_balance = float(Balance())

        # Set volume to higher of 1% of wallet and min bid
        # self.bid_volume = max(self.usd_balance * 0.01 / current_price, 0.002) if current_price else 0.002
        self.bid_volume = 0.002

        # Instantiating a BotTrade object is equivalent to opening a trade. TODO: move open to a function
        if self.trade_type.upper() == 'BUY':
            self._handle_entry_order('buy', current_price)

        if self.trade_type.upper() == 'SELL':
            self._handle_entry_order('sell', current_price)

        statsd.increment('open.order', tags=['name:{}'.format(BOT_NAME),
                                             'pair:{}'.format(self.pair),
                                             'type:{}'.format(self.trade_type),
                                             'order:{}'.format(self.order_type),
                                             'volume:{}'.format(self.bid_volume),
                                             'cur_price:{}'.format(current_price),
                                             'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        statsd.increment('total_trading_volume', self.entry_cost, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        statsd.event(title='Order Open',
                     text='{}/{} - {} {} @ {} / Cost: {}'.format(self.open_order_id, self.pair, self.trade_type, self.bid_volume, self.entry_price, self.entry_cost),
                     alert_type='success',
                     tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        self.output.log("{c1}{trade_type} Trade opened - order_id: {order_id}{c2}".format(c1=Yellow,
                                                                                          trade_type=self.trade_type.upper(),
                                                                                          order_id=self.open_order_id,
                                                                                          c2=White))

        # TODO: Implement trailing stop loss - might be available on Kraken as a special order type
        # TODO: Implement a daily stop loss, 3% of wallet
        self.stop_loss = current_price * (1.0 - (stop_loss_percent / 100)) if stop_loss_percent else 0

    def close(self, current_price):
        self.status = "CLOSED"
        self.close_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        if self.trade_type.upper() == "BUY":
            # Make oppostie trade type to close
            self._handle_exit_order('sell', current_price)

        elif self.trade_type.upper() == "SELL":
            # Make oppostie trade type to close
            self._handle_exit_order('buy', current_price)

        statsd.increment('close.order', tags=['name:{}'.format(BOT_NAME),
                                              'pair:{}'.format(self.pair),
                                              'type:{}'.format(self.trade_type),
                                              'order:{}'.format(self.order_type),
                                              'volume:{}'.format(self.bid_volume),
                                              'cur_price:{}'.format(current_price),
                                              'bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        statsd.event(title='Order Close',
                     text='{}/{} - {} {} @ {} / Cost: {}'.format(self.close_order_id, self.pair, self.trade_type, self.bid_volume, self.exit_price, self.exit_cost),
                     alert_type='success',
                     tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        self.output.log("{c1}{trade_type} Trade closed - order_id: {order_id}{c2}".format(c1=Yellow,
                                                     trade_type=self.trade_type.upper(),
                                                     order_id=self.close_order_id,
                                                     c2=White))

        if self.profit >= 0.0:
            self.output.log("Profit/Loss before fees {}".format(self.profit))
            statsd.increment('bottrade.profit', self.profit, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
            statsd.increment('bottrade.win_rate', 1, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
        else:
            self.output.log("Profit/Loss before fees {}".format(self.profit))
            # Decrement by the absolute value if profit is negative
            statsd.decrement('bottrade.profit', abs(self.profit), tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
            statsd.decrement('bottrade.win_rate', 1, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

        self.output.log("Trade fees at closing: {}".format(self.fees))
        statsd.increment('trading_fees', self.fees, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

    def tick(self, current_price):
        if self.stop_loss:
            if current_price < self.stop_loss:  # TODO: Does this work for short trade?
                self.output.log("Closed on stop loss set to {}".format(self.stop_loss_percent))
                self.close(current_price)

    def show_trade(self):
        trade_status = "{c1}{open_time} / {close_time} {order_id} {c2}{order_type}{c3} {bid_vol} @ {entry_price} = ${cost}{c1} {close_order_id} {status} Exit Price: {exit_price}".format(
            bid_vol=self.bid_volume,
            open_time=self.open_time,
            close_time=self.close_time,
            entry_price=str(self.entry_price),
            cost=str(self.entry_cost),
            status=str(self.status),
            exit_price=str(self.exit_price),
            order_id=str(self.open_order_id),
            close_order_id=str(self.close_order_id),
            order_type=str(self.trade_type),
            c1=Purple,
            c2=Red,
            c3=Cyan)

        # TODO: Refactor
        if self.status == "CLOSED":
            trade_status = trade_status + " P/L: "

            self.exit_minus_entry_less_fees = (self.exit_price - self.entry_price) - self.fees

            if self.exit_minus_entry_less_fees > 0:
                if self.trade_type.upper() == 'BUY':
                    trade_status = trade_status + Green
                elif self.trade_type.upper() == 'SELL':
                    trade_status = trade_status + Red

                self.exit_minus_entry_less_fees = (self.exit_price - self.entry_price) - self.fees

            elif self.exit_minus_entry_less_fees < 0:
                if self.trade_type.upper() == 'BUY':
                    trade_status = trade_status + Red
                elif self.trade_type.upper() == 'SELL':
                    trade_status = trade_status + Green

                self.exit_minus_entry_less_fees = (self.entry_price - self.exit_price) - self.fees

            else:
                trade_status = trade_status + White

            # Percent change in market.
            if self.exit_price > 0:
                self.trade_net_precent = 100 * (float(self.exit_price) - (self.entry_price)) / self.exit_price
                self.trade_pl = round((self.entry_price * self.bid_volume) * (self.trade_net_precent / 100) - self.fees, 4)
            else:
                self.trade_net_precent = 0
                self.trade_pl = 0

            trade_status = trade_status + " $" + str(self.trade_pl) + " | $" + str(self.exit_minus_entry_less_fees) + " (" + str(round(self.trade_net_precent, 3)) + "%)" + White

        self.output.log(trade_status + White)

    @staticmethod
    def get_order_price(order_obj):
        order_id = order_obj.get('result').keys()[0]
        return float(order_obj.get('result', {}).get(order_id, {}).get('price'))

    def get_trade_fee_from_order_object(self, order_obj):
        """
        Given a filled order object extracts the trade fee from the associated trade object.

        :param order_obj = Full order object from calling QueryOrders()
        Returns None if order has not yet been filled.
        Returns trade fee amount in dollars.
        """
        fees = 0.0
        try:
            result = order_obj.get('result', {})
            order_id = next(iter(result))
            trade_id_lst = order_obj.get('result', {}).get(order_id, {}).get('trades')
            for id in trade_id_lst:
                trade = QueryTrades(id)
                result = trade.get('result', {})
                trade_obj = result.get(id, {})
                trade_fee = float(trade_obj.get('fee'))
                fees += trade_fee
            return fees
        except Exception:
            return fees

    def _handle_entry_order(self, trade_type, current_price):
        response = AddOrder(self.pair,
                            trade_type.lower(),
                            self.order_type.lower(),
                            self.bid_volume,
                            round(current_price, 1),
                            userref=self.user_ref_id,
                            validate=VALIDATE)

        # Used in paper trading and backtesting
        if VALIDATE:
            self.entry_price = current_price
            self.entry_cost = self.entry_price * self.bid_volume
            self.fee_percentage = float(TradeVolume().get('result', {}).get('fees', {}).get(self.pair, {}).get('fee', 0.2600)) / 100
            self.output.log("fee_percentage: {}".format(self.fee_percentage))
            self.output.log("Trade entry cost {}".format(self.entry_cost))
            self.fees += float(self.entry_cost) * self.fee_percentage

        if response is not None and not response['error']:
            # Extract order id
            self.open_order_id = response.get('result', {'txid': 'N/A'}).get('txid', 'N/A')[0]
            self.open_order_obj = QueryOrders(self.open_order_id, trades=True)
            if not self.open_order_obj['error']:
                # Extract order price
                self.entry_price = self.get_order_price(self.open_order_obj) if not VALIDATE else current_price * self.bid_volume
                self.entry_cost = self.entry_price * self.bid_volume
                self.output.log("Trade entry cost {}".format(self.entry_cost))
                # Extract fees
                self.fees += self.get_trade_fee_from_order_object(self.open_order_obj) if not VALIDATE else 0.0

            if not __debug__:
                msg = json.dumps(response.get('result', {}))
                slack.post("`{}`\n`Price: {} fee: {} cost: {}`".format(msg, self.entry_price, self.fees, self.entry_cost), username=BOT_NAME)

    def _handle_exit_order(self, trade_type, current_price):
        response = AddOrder(self.pair,
                            trade_type.lower(),
                            self.order_type.lower(),
                            self.bid_volume,
                            round(current_price, 1),
                            userref=self.user_ref_id,
                            validate=VALIDATE)

        # Used in paper trading and backtesting
        if VALIDATE:
            self.exit_price = current_price
            self.exit_cost = self.exit_price * self.bid_volume
            self.output.log("fee_percentage: {}".format(self.fee_percentage))
            self.output.log("Trade entry cost {}".format(self.exit_cost))
            self.profit = self.exit_cost - self.entry_cost
            self.fees += float(self.exit_cost) * float(self.fee_percentage)

        if response is not None and not response['error']:
            # Extract order id.
            self.close_order_id = response.get('result', {'txid': '-'}).get('txid', '-')[0]
            self.close_order_obj = QueryOrders(self.close_order_id, trades=True)
            if not self.close_order_obj['error']:
                # Extract order price
                self.exit_price = self.get_order_price(self.close_order_obj) if not VALIDATE else current_price * self.bid_volume
                self.exit_cost = self.exit_price * self.bid_volume
                self.profit = self.exit_cost - self.entry_cost
                self.output.log("Trade exit cost {}".format(self.entry_cost))
                # Extract fees
                self.fees += self.get_trade_fee_from_order_object(self.close_order_obj) if not VALIDATE else 0

            if not __debug__:
                msg = json.dumps(response.get('result', {}))
                slack.post("`{}`\n`Price: {} fee: {} cost: {}`".format(msg, self.exit_price, self.fees, self.exit_cost), username=BOT_NAME)

    # TODO: Use OpenOrders API call to see not yet filled limit orders
