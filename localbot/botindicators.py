import numpy as np
import talib

class BotIndicators(object):
    """Indicators to use in strategies"""
    def __init__(self):
        pass

    def moving_average(self, dataPoints, period):
        if len(dataPoints) > 1:
            return sum(dataPoints[-period:]) / float(len(dataPoints[-period:]))

    def slope(self, trend_values, lookback=9):
        """Returns the slope of a trendline over a given period"""
        if len(trend_values) >= lookback:
            trend = np.asarray(trend_values, dtype=np.double)
            return talib.LINEARREG_SLOPE(trend, lookback)[-1]

    def momentum(self, dataPoints, period=14):
        if len(dataPoints) > period - 1:
            return dataPoints[-1] * 100 / dataPoints[-period]

    def EMA(self, prices, period):
        prices = np.asarray(prices, dtype=np.double)
        return talib.EMA(prices, period)[-1:]

    def MACD(self, prices, slow=26, fast=12, signal=9):
        if len(prices) > slow + signal:
            prices = np.asarray(prices, dtype=np.double)
            macd, signal, hist = talib.MACD(prices, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            macd = macd[~np.isnan(macd)]
            signal = signal[~np.isnan(signal)]
            hist = hist[~np.isnan(hist)]
            return macd, signal, hist

    def STOCH(self, high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0):
        high = np.asarray(high, dtype=np.double)
        low = np.asarray(low, dtype=np.double)
        close = np.asarray(close, dtype=np.double)
        slowk, slowd = talib.STOCH(high, low, close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
        slowk = slowk[~np.isnan(slowk)]
        slowd = slowd[~np.isnan(slowd)]
        return slowk, slowd

    def SAR(self, high, low, acceleration=0.2, maximum=0.2):
        high = np.asarray(high, dtype=np.double)
        low = np.asarray(low, dtype=np.double)
        sar = talib.SAR(high, low, acceleration, maximum)
        sar = sar[~np.isnan(sar)]
        return sar

    def support_resistance(self, ltp, n):
        """
        This function takes a numpy array of last traded price (ltp)
        and returns a list of support and resistance levels
        respectively. n is the number of entries to be scanned,
        aka the lookback. A higher n value will cause more smoothing
        and vice versa.
        """
        from scipy.signal import savgol_filter as smooth

        ltp = np.asarray(ltp, dtype=np.double)

        # Converting n to a nearest even number
        if n % 2 != 0:
            n += 1

        n_ltp = ltp.shape[0]

        # Smooth the curve
        ltp_s = smooth(ltp, (n + 1), 3)

        # Taking a simple derivative
        ltp_d = np.zeros(n_ltp)
        ltp_d[1:] = np.subtract(ltp_s[1:], ltp_s[:-1])

        resistance = []
        support = []

        for i in xrange(n_ltp - n):
            arr_sl = ltp_d[i:(i+n)]
            first = arr_sl[:(n/2)] # First half
            last = arr_sl[(n/2):] # Second half

            r_1 = np.sum(first > 0)
            r_2 = np.sum(last < 0)

            s_1 = np.sum(first < 0)
            s_2 = np.sum(last > 0)

            # Local maxima detection
            if (r_1 == (n/2)) and (r_2 == (n/2)):
                resistance.append(ltp[i+((n/2)-1)])

            # Local minima detection
            if (s_1 == (n/2)) and (s_2 == (n/2)):
                support.append(ltp[i+((n/2)-1)])

        return support, resistance