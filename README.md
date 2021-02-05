An automated trading bot that buys and sells cryptocurrencies on the Kraken exchange.
Only works with Kraken, but general structure and flow could be ported to other exchanges. Requires Kraken key and API access.
Live trading and back testing.
Trading bot runs on Python 2.7.13. Collector bot runs on Python 3.6.4.
Runs on t2.micro AWS instance.
Slack and Datadog integrations.
Each bot is given a unique ID based on its name (top level directory name). This is used for log file names and Datadog metrics.



Class Structure and data flow
![Class Structure and data flow](https://github.com/[jstep]/[trading_bot]/blob/TradingBotClassStructure.png?raw=true)

localbot
bot.py - The main entry point for the trading bot.
botlog.py - Logging class called by most other classes to add functionality above simple logging
botchart.py - Object representing collection of candlestick objects.
botcandlestick.py - Object representing a single candlestick. Includes Open, High, Low, and Close price.
botindicators.py - Technical analysis indicators used by bots. 
botstrategy.py - Base class for all strategy classes.
bottrade.py - Handles all trade actions. Called by strategies.
Colours.py - Some colours to make the console output nicer.
Constants.py - Constants available to all classes. Contains validation flag to control paper/live trading.

Output & Logs
Log file names are a concatenation of the bot ID + the bot name + date started + random 6 letters (to avoid name collisions).

All logs are saved to the logs folder of a given bot.

Ticker - Sample output:
2018-04-17 14:42:55,432:INFO: Open: 7915.5 Close: None High: 7915.5 Low: 7915.5 Current: 7915.5

Ledger - Sample output (will appear all on one line):
2018-04-17 21:45:12,617		← Log timestamp
:INFO:				← Log level
2018-04-13 14:54:50 /		← Trade open timestamp
2018-04-15 11:08:10 		← Trade close timestamp
O534UO-LTVCP-6NNUMC 		← Open order id (from Kraken)
BUY 					← Side. (SELL if shorting)
0.002 				← Trade/order volume
@ 8121.2 				← Trade/order entry price
= $16.2424				← Trade/order cost (price x volume)
OSR3G5-THKZ5-CYHFVJ		← Close order id (from Kraken)
CLOSED 				← Trade status (managed internally by bot)
Exit Price: 8364.2		← Trade/order exit price
P/L:  $0.3862 |			← Profit/Loss of trade
$242.91428				← Abs. +/- movement of market during trade
(2.905%)				← Percentage movement of market during trade

The bot ledger is shown after every strategy tick, i.e. every time a new candlestick is created.
Strategies
All strategies inherit from the BotStrategy base class. Base class includes getting historical prices so indicators can work, showing trades (ledger), updating open trades (tick), and some initializations of methods and parameters. The parameter num_simultaneous_trades controls how many trades can be open at a given time by the bot. 
Strategy flags control entry and exit behaviour on a given strategy. 
The tick() method collects needed data (from a candlestick object) for the indicator to work then shows it, and calls methods to evaluate, update, and show each position. 
The evaluate_positions() method checks if criteria are met to open or close a position. If so, it calls BotTrade class to handle it.
The update_open_trades() method and show_positions() methods are called from the base class.
There are multiple strategy classes, usually named after the main indicator that it uses. Each strategy class implements the logic around opening or closing a position manually. I never got around to implementing short selling, as it requires using leverage on Kraken. 

Indicators
Indicators represent a statistical approach to technical analysis as opposed to a subjective approach. By looking at money flow, trends, volatility, and momentum, they provide a secondary measure to actual price movements and help confirm the quality of chart patterns or form their own buy or sell signals.
The BotIndicators class holds all the indicators used by the strategies. Some are direct manipulations of the data, but most are facades for the TA-Lib Python wrapper (v. 0.4.10). These facades do length checks, conversion to numpy array format, compute the TA-lib indicator, and drop NaNs from the resulting array.

Trade
The BotTrade Class handles all trades made with an exchange and keeps track of open and closed trades made during the current run of the bot. 
Only market orders are supported. Limit orders could be implemented but would require handling orders that have been placed but not filled yet, hand how those would be represented by the bot’s output.
Fees are handled appropriately within this class. All metrics are sent to StatsD (Datadog).
Services
Krakenex/Krakenex3 - Public/Private
	I made some wrapper functions to make using the Krakenex library easier.
Datadog
	All indicator and trade values are sent to DataDog via StatsD.
Slack
	Trade info is sent to a private Slack Channel (reporting)

Deployment
	Rsync
Rsync is a file copying tool used to move local development files to a remote EC2 instance.
rsync -rave 'ssh -i ~/.ssh/trading.pem' ~/path/to/bot/folder ec2-user@ec2-35-163-52-214.us-west-2.compute.amazonaws.com:/home/ec2-user/all_bots
Operations
Running locally & CLI Flags - 
To run a bot from your local machine (or any remote machine) simply run it as a Python script:
python bot.py 

There are also a number of flags that control bot operation:
python -O bot.py -x kraken -p 5 -t 5 -c XXBTZUSD

-O  This is a Python flag that optimizes compiled files. Creates pyo files instead of pyc
-x  Exchange to trade on. Only supports Kraken.
-p  Candlestick period in minutes. The bot will evaluate the strategy after this period.
-t  Ticker polling interval in seconds.
-c  Currency pair. Must match a valid pair name from the exchange.
-s  Start time. Used for backtesting.
-e  End time. Used for backtesting.

Supervisor -
Supervisor is a client/server system that allows its users to monitor and control a number of processes on UNIX-like operating systems. Supervisor is responsible for starting each Python process for running a bot. This allows you to control one thing (supervisor) which controls many things (e.g. Python processes) on your behalf. A conf file registers each process for supervisor to run. On the EC2 instance I kept the conf file at ~/anaconda/etc/supervisord/conf.d/all_bots.conf but this can be changed. A typical conf file process looks like this:
[program:itchbot]
command=python -O bot.py -x kraken -p 5 -t 5 -c XXBTZUSD
directory=/home/ec2-user/all_bots/itchbot/
autostart=yes
autorestart=yes
startretries=3
logfile=/var/log/supervisor/supervisord.log
user=ec2-user
environment=DATADOG_API_KEY="DD API_KEY",DATADOG_APP_KEY="DD APP_KEY"
Future
Create an idempotent solution for API calls to Kraken.
Store trades in DB. Read on startup/restart to have a ‘memory’ of trades open.
Use machine learning on the order book database to predict market movement. 


Appendix

File structure

├── __init__.py
├── collector
│   ├── __init__.py
│   ├── database
│   │   ├── __init__.py
│   │   └── db_create_table_for_pair.py
│   ├── get_orderbook_async.py
│   ├── orderbook_collector_bot.py
│   └── scripts
│       ├── __init__.py
│       ├── async_test.py
│       └── krakenBTCUSDpriceToFile.py
├── exchanges
│   ├── __init__.py
│   ├── krakenex
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── connection.py
│   │   ├── kraken.key
│   │   ├── private.py
│   │   └── public.py
│   └── krakenex_py3
│       ├── __init__.py
│       ├── api.py
│       ├── kraken.key
│       ├── public.py
│       └── version.py
├── kraken.key
├── localbot
│   ├── __init__.py
│   ├── bot.py
│   ├── botcandlestick.py
│   ├── botchart.py
│   ├── botindicators.py
│   ├── botlog.py
│   ├── bottrade.py
│   ├── colours.py
│   ├── constants.py
│   ├── logs
│   │   └── 320:Localbot_2018-04-17_21_umpmen
│   ├── strategy
│   │   ├── __init__.py
│   │   ├── botstrategy.py
│   │   ├── macd.py
│   │   ├── macd_strategy.py
│   │   ├── parabolic_sar_stochastic.py
│   │   ├── stochastic.py
│   │   └── stochastic_sr_ma.py
│   └── utils
│       ├── __init__.py
│       └── services
│           ├── __init__.py
│           ├── metrics.py
│           └── slack.py
└── rsync

