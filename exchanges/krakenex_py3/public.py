import os
import sys

from .api import API

# __location__ = os.path.realpath(
#     os.path.join(os.getcwd(), os.path.dirname(__file__)))
#
# conn = API()
# # conn.load_key('kraken.key')
# # key_file = open('kraken.key')
# print(sys.path[0])
# key_file = open(os.path.join(sys.path[0], "kraken.key"), "r")
# conn.key = key_file

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

conn = API()
# conn.load_key('kraken.key')  # TODO: notebook
key_file = open(os.path.join(__location__, 'kraken.key'))  # TODO: ENV VAR
conn.key = key_file


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

    res = dict((k, v) for k, v in locals().items() if v is not None)
    while True:
        try:
            return conn.query_public(_fname, res, timeout=30)
        except Exception as err:
            print('Failed to get {}: {}'.format(_fname, err))
            continue