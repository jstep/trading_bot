import logging
import os
import random
import string
from datetime import datetime

from constants import BOT_ID, BOT_NAME

CURSOR_UP_ONE_LINE = '\033[F'
CURSOR_START_OF_LINE = '\r'


class BotLog(object):
    def __init__(self):
        self.utc_datetime = datetime.utcnow()
        directory = "{}/logs".format(os.getcwd())
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Generate a random string to append to the log file name.
        rand_str = lambda n: ''.join([random.choice(string.lowercase) for i in xrange(n)])

        logging.basicConfig(filename="logs/{}:{}_{}_{}".format(
            BOT_ID,
            BOT_NAME,
            self.utc_datetime.strftime("%Y-%m-%d_%H"),
            rand_str(6)),
            level=logging.INFO,
            format="%(asctime)s:%(levelname)s:%(message)s")

    @staticmethod
    def log(message):
        print message
        logging.info(message)

    # def chart(self, data):
    #     self.output_.write("""]);var options = {title: ' XXBTZUSD Price Chart',legend: { position: 'bottom' }};var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));chart.draw(data, options);}</script></head><body><div id="curve_chart" style="width: 100%; height: 100%"></div></body></html>""")

