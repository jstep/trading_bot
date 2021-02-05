import sys
import urllib2
import logging
import os

from api import API as KrakenAPI

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

conn = KrakenAPI()
# conn.load_key('kraken.key')  # TODO: notebook
key_file = open(os.path.join(__location__, 'kraken.key'))  # TODO: ENV VAR
conn.key = key_file

logger = logging.getLogger()

# Function and parameters must match API endpoint in name and case. add_order != AddOrder.


def AddOrder(pair, type, ordertype, volume, price=None, price2=None,
             leverage=None, oflags=None, starttm=None, expiretm=None,
             userref=None, validate=True):
    """
    Open or Close a position

    Input:
        pair = asset pair
        type = type of order (buy/sell)
        ordertype = order type:
            market
            limit (price = limit price)
            stop-loss (price = stop loss price)
            take-profit (price = take profit price)
            stop-loss-profit (price = stop loss price, price2 = take profit price)
            stop-loss-profit-limit (price = stop loss price, price2 = take profit price)
            stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
            take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
            trailing-stop (price = trailing stop offset)
            trailing-stop-limit (price = trailing stop offset, price2 = triggered limit offset)
            stop-loss-and-limit (price = stop loss price, price2 = limit price)
            settle-position
        price = price (optional.  dependent upon ordertype)
        price2 = secondary price (optional.  dependent upon ordertype)
        volume = order volume in lots
        leverage = amount of leverage desired (optional.  default = none)
        oflags = comma delimited list of order flags (optional):
            viqc = volume in quote currency (not available for leveraged orders)
            fcib = prefer fee in base currency
            fciq = prefer fee in quote currency
            nompp = no market price protection
            post = post only order (available when ordertype = limit)
        starttm = scheduled start time (optional):
            0 = now (default)
            +<n> = schedule start time <n> seconds from now
            <n> = unix timestamp of start time
        expiretm = expiration time (optional):
            0 = no expiration (default)
            +<n> = expire <n> seconds from now
            <n> = unix timestamp of expiration time
        userref = user reference id.  32-bit signed number.  (optional)
        validate = validate inputs only.  do not submit order (optional)

        optional closing order to add to system when order gets filled:
            close[ordertype] = order type
            close[price] = price
            close[price2] = secondary price

    Result:
        descr = order description info
            order = order description
            close = conditional close order description (if conditional close set)
        txid = array of transaction ids for order (if order was added successfully)
    """

    if not validate:
        validate = None
    _fname = sys._getframe().f_code.co_name

    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)

    # Retry AddOrder call only once.
    for i in range(0, 1):
        try:
            # Place the order
            return conn.query_private(_fname, res)
        except urllib2.ssl.SSLError, err:
            # For read timeouts
            logger.warn("{}... Retry {}".format(err, _fname))
            continue
        except urllib2.URLError, err:
            # If network or site is down
            logger.warn("{}... Retry {}".format(err, _fname))
            continue
        except ValueError, err:
            # For screwy JSON
            logger.warn('{}... Retry {}'.format(err, _fname))
            continue
    return {u'error': [err]}


def CancelOrder(txid):
    """
    Cancel open order
    Note: txid may be a user reference id.

    :param txid = transaction id

    :return: count = number of orders canceled
             pending = if set, order(s) is/are pending cancellation
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def Balance(aclass=None, asset='ZUSD'):
    """
    Get account balance
    Result: array of asset names and balance amount
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)
    try:
        return conn.query_private(_fname)['result'][asset]
    except Exception as err:
        logger.warn('Failed to get {}: {}'.format(_fname, err))
        logger.warn('Returning 0.0')
        return 0.0


def TradeBalance(aclass=None, asset='ZUSD'):
    """
    Get trade balance
    Result: array of trade balance info

    Note: Rates used for the floating valuation is the midpoint of the best bid and ask prices
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def OpenOrders(trades=False, userref=None):
    """
    Get open orders
    Result: array of order info in open array with txid as the key

    Note: Unless otherwise stated, costs, fees, prices, and volumes are
    in the asset pair's scale, not the currency's scale. For example,
    if the asset pair uses a lot size that has a scale of 8, the volume
    will use a scale of 8, even if the currency it represents only has a
    scale of 2. Similarly, if the asset pair's pricing scale is 5, the
    scale will remain as 5, even if the underlying currency has a scale of 8.

    refid = Referral order transaction id that created this order
    userref = user reference id
    status = status of order:
        pending = order pending book entry
        open = open order
        closed = closed order
        canceled = order canceled
        expired = order expired
    opentm = unix timestamp of when order was placed
    starttm = unix timestamp of order start time (or 0 if not set)
    expiretm = unix timestamp of order end time (or 0 if not set)
    descr = order description info
        pair = asset pair
        type = type of order (buy/sell)
        ordertype = order type (See Add standard order)
        price = primary price
        price2 = secondary price
        leverage = amount of leverage
        order = order description
        close = conditional close order description (if conditional close set)
    vol = volume of order (base currency unless viqc set in oflags)
    vol_exec = volume executed (base currency unless viqc set in oflags)
    cost = total cost (quote currency unless unless viqc set in oflags)
    fee = total fee (quote currency)
    price = average price (quote currency unless viqc set in oflags)
    stopprice = stop price (quote currency, for trailing stops)
    limitprice = triggered limit price (quote currency, when limit based order type triggered)
    misc = comma delimited list of miscellaneous info
        stopped = triggered by stop price
        touched = triggered by touch price
        liquidated = liquidation
        partial = partial fill
    oflags = comma delimited list of order flags
        viqc = volume in quote currency
        fcib = prefer fee in base currency (default if selling)
        fciq = prefer fee in quote currency (default if buying)
        nompp = no market price protection
    trades = array of trade ids related to order (if trades info requested and data available)
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def ClosedOrders(trades=False, userref=None, start=None, end=None, ofs=None, closetime='both'):
    """
    Get closed orders
    Result: array of order info
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def QueryOrders(txid, trades=False, userref=None):
    """
    Query orders info
    Result: associative array of orders info

    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)

    # Retry API call until successful.
    # for i in range(0, 1):
    while True:
        try:
            # Place the order
            return conn.query_private(_fname, res)
        except urllib2.ssl.SSLError, err:
            # For read timeouts
            logger.warn("{}... Retry {}".format(err, _fname))
            continue
        except urllib2.URLError, err:
            # If network or site is down
            logger.warn("{}... Retry {}".format(err, _fname))
            continue
        except ValueError, err:
            # For screwy JSON
            logger.warn('{}... Retry {}'.format(err, _fname))
            continue
    return {u'error': [err]}


def TradesHistory(type='all', trades=False, start=None, end=None, ofs=None):
    """
    Get trades history
    Result: array of trade info

    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def QueryTrades(txid, trades=False):
    """
    Query trades info
    Result: associative array of trades info

    Note: Unless otherwise stated, costs, fees, prices, and volumes are in the asset pair's scale, not the currency's scale.
    Times given by trade tx ids are more accurate than unix timestamps.

    trades = array of trade info with txid as the key
        ordertxid = order responsible for execution of trade
        pair = asset pair
        time = unix timestamp of trade
        type = type of order (buy/sell)
        ordertype = order type
        price = average price order was executed at (quote currency)
        cost = total cost of order (quote currency)
        fee = total fee (quote currency)
        vol = volume (base currency)
        margin = initial margin (quote currency)
        misc = comma delimited list of miscellaneous info
            closing = trade closes all or part of a position
    count = amount of available trades info matching criteria

    If the trade opened a position, the follow fields are also present in the trade info:

        posstatus = position status (open/closed)
        cprice = average price of closed portion of position (quote currency)
        ccost = total cost of closed portion of position (quote currency)
        cfee = total fee of closed portion of position (quote currency)
        cvol = total fee of closed portion of position (quote currency)
        cmargin = total margin freed in closed portion of position (quote currency)
        net = net profit/loss of closed portion of position (quote currency, quote currency scale)
        trades = list of closing trades for position (if available)

    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def OpenPositions(txid=None, docalcs=False):
    """
    Get open positions
    Result: associative array of open position info

    Note: Unless otherwise stated, costs, fees, prices,
    and volumes are in the asset pair's scale, not the currency's scale

    <position_txid> = open position info
    ordertxid = order responsible for execution of trade
    pair = asset pair
    time = unix timestamp of trade
    type = type of order used to open position (buy/sell)
    ordertype = order type used to open position
    cost = opening cost of position (quote currency unless viqc set in oflags)
    fee = opening fee of position (quote currency)
    vol = position volume (base currency unless viqc set in oflags)
    vol_closed = position volume closed (base currency unless viqc set in oflags)
    margin = initial margin (quote currency)
    value = current value of remaining position (if docalcs requested.  quote currency)
    net = unrealized profit/loss of remaining position (if docalcs requested.  quote currency, quote currency scale)
    misc = comma delimited list of miscellaneous info
    oflags = comma delimited list of order flags
        viqc = volume in quote currency
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def Ledgers(aclass=None, asset='all', type='all', start=None, end=None, ofs=None):
    """
    Get ledgers info
    Result: associative array of ledgers info

    <ledger_id> = ledger info
    refid = reference id
    time = unx timestamp of ledger
    type = type of ledger entry
    aclass = asset class
    asset = asset
    amount = transaction amount
    fee = transaction fee
    balance = resulting balance
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def QueryLedgers(id):
    """
    Query ledgers
    Result: associative array of ledgers info
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)


def TradeVolume(pair='XXBTZUSD', fee_info=None):
    """
    Get trade volume
    Result: associative array

    currency = volume currency
    volume = current discount volume
    fees = array of asset pairs and fee tier info (if requested)
        fee = current fee in percent
        minfee = minimum fee for pair (if not fixed fee)
        maxfee = maximum fee for pair (if not fixed fee)
        nextfee = next tier's fee for pair (if not fixed fee.  nil if at lowest fee tier)
        nextvolume = volume level of next tier (if not fixed fee.  nil if at lowest fee tier)
        tiervolume = volume level of current tier (if not fixed fee.  nil if at lowest fee tier)
    fees_maker = array of asset pairs and maker fee tier info (if requested) for any pairs on maker/taker schedule
        fee = current fee in percent
        minfee = minimum fee for pair (if not fixed fee)
        maxfee = maximum fee for pair (if not fixed fee)
        nextfee = next tier's fee for pair (if not fixed fee.  nil if at lowest fee tier)
        nextvolume = volume level of next tier (if not fixed fee.  nil if at lowest fee tier)
        tiervolume = volume level of current tier (if not fixed fee.  nil if at lowest fee tier)
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_private(_fname, res)