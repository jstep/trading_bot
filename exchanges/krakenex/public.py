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


def Ticker(pair='XXBTZUSD'):
    """
    Get ticker information
    Result: array of pair names and their ticker info

    Note: Today's prices start at 00:00:00 UTC

    :param pair = comma delimited list of asset pairs to get info on

    :returns
        <pair_name> = pair name
        a = ask array(<price>, <whole lot volume>, <lot volume>),
        b = bid array(<price>, <whole lot volume>, <lot volume>),
        c = last trade closed array(<price>, <lot volume>),
        v = volume array(<today>, <last 24 hours>),
        p = volume weighted average price array(<today>, <last 24 hours>),
        t = number of trades array(<today>, <last 24 hours>),
        l = low array(<today>, <last 24 hours>),
        h = high array(<today>, <last 24 hours>),
        o = today's opening price
    """
    _fname = sys._getframe().f_code.co_name

    # Must drop None values for API call succeed.
    res = dict((k,v) for k, v in locals().iteritems() if v is not None)
    while True:
        try:
            return conn.query_public(_fname, res)
        except Exception as err:
            print('Failed to get {}: {}'.format(_fname, err))
            continue


def OHLC(pair='XXBTZUSD', interval=1, since=None):
    """
    Get OHLC data
    Result: array of pair name and OHLC data

    :param: pair = asset pair to get OHLC data for.
    :param: interval = time frame interval in minutes (optional):
            1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
    :param: since = return committed OHLC data since given id (optional.  exclusive)

    :return: <pair_name> = pair name
                array of array entries(<time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>)
            last = id to be used as since when polling for new, committed OHLC data
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)
    # logger.info("Fetching historical OHLC data...CAT")
    while True:
        try:
            return conn.query_public(_fname, res)
        except urllib2.ssl.SSLError, err:
            # For read timeouts
            logger.warn('{}... Retry {}'.format(err, _fname))
            continue
        except urllib2.URLError, err:
            # If network or site is down
            logger.warn('{}... Retry {}'.format(err, _fname))
            continue
        except ValueError, err:
            # For screwy JSON
            logger.warn('{}... Retry {}'.format(err, _fname))
            continue


def Time(unixtime=None, rfc1123=None):
    """
    Get server time
    Note: This is to aid in approximating the skew time between the server and client.

    :param unixtime =  as unix timestamp
    :param rfc1123 = as RFC 1123 time format
    :return Server's time

    """
    _fname = sys._getframe().f_code.co_name

    # Must drop None values for API call succeed.
    res = dict((k,v) for k, v in locals().iteritems() if v is not None)
    return conn.query_public(_fname, res)


def Depth(pair='XXBTZUSD', count=None):
    """
    Get order book
    Result: array of pair name and market depth

    :param pair = asset pair to get market depth for
    :param count = maximum number of asks/bids (optional)

    :returns <pair_name> = pair name
                asks = ask side array of array entries(<price>, <volume>, <timestamp>)
                bids = bid side array of array entries(<price>, <volume>, <timestamp>)
    :return None if API fails
    """
    _fname = sys._getframe().f_code.co_name

    # Must drop None values for API call succeed.
    res = dict((k,v) for k, v in locals().iteritems() if v is not None)
    while  True:
        try:
            return conn.query_public(_fname, res)
        except Exception as err:
            print('Failed to get {}: {}'.format(_fname, err))
            continue


def Spread(pair='XXBTZUSD', since=None):
    """
    Get recent spread data
    The bid/ask spread is the difference in price between the highest bid
    and the lowest ask on the order book.
    Result: array of pair name and recent trade data

    :param pair = asset pair to get spread data for
    :param since = return spread data since given id (optional.  inclusive)

    :returns <pair_name> = pair name
                array of array entries(<time>, <bid>, <ask>)
            last = id to be used as since when polling for new spread data
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k, v) for k, v in locals().iteritems() if v is not None)
    try:
        return conn.query_public(_fname, res)
    except KeyError as err:
        print('Failed to get {}: {}'.format(_fname, err))
        return None


def Assets(info=None, aclass=None, asset=None):
    """
    Get asset info
    Result: array of asset names and their info
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_public(_fname, res)

def AssetPairs(info=None, pair=None):
    """
    Get tradable asset pairs
    Result: array of pair names and their info

    Note: If an asset pair is on a maker/taker fee schedule,
    the taker side is given in "fees" and maker side in "fees_maker".
    For pairs not on maker/taker, they will only be given in "fees".
    """
    _fname = sys._getframe().f_code.co_name
    # Must drop None values for API call succeed.
    res = dict((k,v) for k,v in locals().iteritems() if v is not None)
    return conn.query_public(_fname, res)