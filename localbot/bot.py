import getopt
import sys
import time
import urllib2

from datadog import statsd

from botcandlestick import BotCandlestick
from botchart import BotChart
from botlog import BotLog
from colours import *
from constants import BOT_ID, BOT_NAME


# Strategy Imports
from strategy import (
    MACDStrategy
)


def main(argv):
    """
    Main entry point
    """

    # Logging
    output = BotLog()

    supported_exchanges = ['kraken']
    exchange = 'kraken'
    pair = "XXBTZUSD"  # Bitcoin/USD pair on Kraken

    period = 5  # Time frame interval in minutes, e.g. width of candlestick.
    poll_time = 1  # How often an API query is made when using real time data.

    script_help = '\n\t-c --currency <currency pair>\n\t-x --exchange <name of the exchange {exchanges}>\n\t-t --poll <poll period length in minutes>\n\nHistorical Mode\n\t-p --period <period of frame>\n\t-s --start <start time in unix timestamp>\n\t-e --end <end time in unix timestamp>\n'.format(exchanges=supported_exchanges)

    start_time = False
    end_time = False

    try:
        opts, args = getopt.getopt(argv, "h:x:p:c:t:s:e:y:", ["exchange=", "period=", "currency=", "poll=", "start=", "end="])
    except getopt.GetoptError:
        output.log(sys.argv[0] + script_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt == ("-h", "--help"):
            output.log(sys.argv[0] + script_help)
            sys.exit()
        elif opt in ("-s", "--start"):
            start_time = arg
        elif opt in ("-e", "--end"):
            end_time = arg
        elif opt in ("-x", "--exchange"):
            if arg in supported_exchanges:
                exchange = arg
            else:
                output.log('Supported exchanges are {}'.format(supported_exchanges))
                sys.exit(2)
        elif opt in ("-p", "--period"):
            if exchange.lower() == 'kraken':
                # Kraken uses minutes for getting historical data.
                mins = [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
                if (int(arg) in mins):
                    period = int(arg)
                else:
                    output.log('Kraken requires intervals 1, 5, 15, 30, 60, 240, 1440, 10080, 21600 minute intervals')
                    sys.exit(2)
            else:
                period = int(arg)
        elif opt in ("-c", "--currency"):
            pair = arg
        elif opt in ("-t", "--poll"):
            poll_time = arg

    ################ Strategy in use ################
    strategy = MACDStrategy(pair, period)
    strategy_name = strategy.get_name()
    #################################################

    # Log bot startup event to DataDog
    statsd.event(title='Bot started',
                 text='{}:{} started on {} trading {} using {}'.format(BOT_ID, BOT_NAME, exchange, pair, strategy_name),
                 alert_type='success', tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])

    trade_session_details = "{bg}Trading {pair} on {exchange} with {strat}" \
                            " @ {period} minute period{White}".format(pair=pair,
                                                                      exchange=exchange.upper(),
                                                                      strat=strategy_name,
                                                                      period=period,
                                                                      bg=On_Cyan,
                                                                      White=White)

    if start_time:
        # Backtesting
        chart = BotChart(exchange, pair, period)
        for candlestick in chart.get_points():
            strategy.tick(candlestick)

        output.log(trade_session_details)

    else:
        # Live Trading
        output.log(trade_session_details)

        chart = BotChart(exchange, pair, period, backtest=False)

        candlesticks = []
        developing_candlestick = BotCandlestick(period)

        progress_counter = 0
        while True:
            # Log trade details every so often
            if progress_counter == 50:
                output.log(trade_session_details)
                progress_counter = 0
            progress_counter += 1

            try:
                developing_candlestick.tick(chart.get_current_price_and_vol()[0])
            except urllib2.URLError, err:
                # If network or site is down
                output.log("{}... Continuing".format(err[0]))
                # TODO: These calls to statsd should be Rollbar. Set up Rollbar
                statsd.histogram('main_loop.urllib2.URLError', err, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
                continue
            except ValueError, err:
                # For screwy JSON
                output.log('{}... Continuing'.format(err[0]))
                statsd.histogram('main_loop.ValueError', err, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
                continue
            except urllib2.ssl.SSLError, err:
                # For read timeouts
                output.log("{}... Continuing".format(err[0]))
                statsd.histogram('main_loop.urllib2.ssl.SSLError', err, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
                continue
            except Exception as err:
                # Something else happened but we still want ot log it, send it to DD, and keep going.
                output.log("Unexpected error: {}".format(sys.exc_info()[0]))
                statsd.histogram('main_loop.unknown_exception', err, tags=['bot_name:{}.bot_id:{}'.format(BOT_NAME, BOT_ID)])
                time.sleep(30)
                continue

            #  When close price is present
            if developing_candlestick.isClosed():
                # Add the closed candlestick to the list
                candlesticks.append(developing_candlestick)
                # Enact the strategy
                strategy.tick(developing_candlestick)
                # Create a new candlestick
                developing_candlestick = BotCandlestick(period)

            time.sleep(float(poll_time))

if __name__ == "__main__":
    main(sys.argv[1:])
