import os

# global settings and parameters

# Get the folder name to use as the bot name.
BOT_NAME = os.path.dirname(os.path.realpath(__file__)).split('/')[-1].title()

# BOT_ID is a 3 digit hash of BOT_NAME
# Prepended to each userref to identify which trades made by a given bot.
BOT_ID = abs(hash(BOT_NAME)) % (10 ** 3)

# Controls live/paper trading.
# VALIDATE True means dry run. If set to False, real trades will be made!
VALIDATE = True