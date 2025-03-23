import numpy as np
import pandas as pd
from backtesting import Strategy

def ema(prices, minutes, smoothingMinutes):
    raw = pd.DataFrame(prices).rolling(window=minutes, win_type='exponential').mean()
    return raw.rolling(window=smoothingMinutes, win_type='exponential').mean()

def initSeries(prices):
    return pd.Series(prices)

class LiveStrategy(Strategy):

    # optimization params
    fastMinutes = 25
    disableEntryMinutes = 0
    fastMomentumMinutes = 110
    fastCrossoverPercent = 0.40
    takeProfitPercent = 0
    fastAngleFactor = 20
    slowMinutes = 1555
    slowAngleFactor = 20
    entryRestrictionMinutes = 15
    entryRestrictionPercent = 0

    coolOffMinutes = 5
    positionEntryMinutes = 1

    fastAngle = fastAngleFactor / 1000.0
    slowAngle = slowAngleFactor / 1000.0
    takeProfit = takeProfitPercent / 100.0

    fastCrossover = (fastCrossoverPercent / 100.0) * takeProfit
    if takeProfit == 0:
        fastCrossover = fastCrossoverPercent / 100.0

    def init(self):

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        ohlc4 = (open + high + low + close) / 4

        # exponential moving average
        self.fast = self.I(ema, open, self.fastMinutes, 5)
        self.slow = self.I(ema, open, self.slowMinutes, 200)

        # horizontal price lines
        self.longFastCrossoverExit = self.I(initSeries, ohlc4)
        self.shortFastCrossoverExit = self.I(initSeries, ohlc4)
        self.longTakeProfit = self.I(initSeries, ohlc4)
        self.shortTakeProfit = self.I(initSeries, ohlc4)

    def next(self):

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        disableEntryMinutes = self.disableEntryMinutes
        slowAngle = self.slowAngle
        position = self.position
        is_long = self.position.is_long
        is_short = self.position.is_short
        fastCrossover = self.fastCrossover
        fastMomentumMinutes = self.fastMomentumMinutes
        fastAngle = self.fastAngle
        takeProfit = self.takeProfit

        normalizedFastPrice = ((self.fast - self.fast[-1]) / self.fast[-1]) * 100
        normalizedSlowPrice = ((self.slow - self.slow[-1]) / self.slow[-1]) * 100
        fastSlope = np.rad2deg(np.arctan(normalizedFastPrice))
        slowSlope = np.rad2deg(np.arctan(normalizedSlowPrice))

        # price crosses through fast average in favorable direction
        isFastCrossoverLong = (
            (fastSlope > self.fastAngle
            and (self.fast > open or self.fast > close[-1]))
            and high > self.fast)
        isFastCrossoverShort = (
            (-self.fastAngle > fastSlope
            and (open > self.fast or close[-1] > self.fast))
            and self.fast > low)

        # allow entry only during starting minutes of trend
        if disableEntryMinutes == 0:
            isEntryLongDisabled = False
            isEntryShortDisabled = False
        else:
            isEntryLongDisabled = True if np.min(fastSlope, disableEntryMinutes) > 0 else False
            isEntryShortDisabled = True if 0 > np.max(fastSlope, disableEntryMinutes) else False

        # todo handle short volatility

        # todo cooloff time

        # todo entry restriction idea

        # entries
        isEntryLong = (
            position == 0
            and isFastCrossoverLong
            and not isEntryLongDisabled
            and slowSlope > slowAngle)
        isEntryShort = (
            position.size == 0
            and isFastCrossoverShort
            and not isEntryShortDisabled
            and -slowAngle > slowSlope)

        # exit crossing back into fast in unfavorable direction
        if is_long:
            self.longFastCrossoverExit = self.longFastCrossoverExit[-1]
        if isEntryLong:
            self.longFastCrossoverExit = (1 + fastCrossover) * self.fast
        if is_short:
            self.shortFastCrossoverExit = self.shortFastCrossoverExit[-1]
        if isEntryShort:
            self.shortFastCrossoverExit = (1 - fastCrossover) * self.fast

        isExitLongFastCrossoverEnabled = True if is_long and high > self.longFastCrossoverExit else False
        isExitShortFastCrossoverEnabled = True if is_short and self.shortFastCrossoverExit > low else False

        isExitLongFastCrossover = True if (
            isExitLongFastCrossoverEnabled
            and is_long
            and self.fast > low) else False

        isExitShortFastCrossover = True if (
            isExitShortFastCrossoverEnabled
            and is_short
            and high > self.fast) else False

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = True if (
                fastMomentumMinutes != 0
                and is_long
                and -fastAngle > np.max(fastSlope, fastMomentumMinutes)) else False

        isExitShortFastMomentum = True if (
            fastMomentumMinutes != 0
            and is_short
            and np.min(fastSlope, fastMomentumMinutes) > fastAngle) else False

        # take profit
        if is_long:
            self.longTakeProfit = self.longTakeProfit[-1]
        elif isEntryLong and self.takeProfit != 0:
            self.longTakeProfit = (1 + takeProfit) * self.fast

        if is_short:
            self.shortTakeProfit = self.shortTakeProfit[-1]
        elif isEntryShort and takeProfit != 0:
            self.shortTakeProfit = (1 - takeProfit) * self.fast

        isExitLongTakeProfit = True if (
            is_long
            and high > self.longTakeProfit
        ) else False

        isExitShortTakeProfit = True if (
            is_short
            and self.shortTakeProfit > low
        ) else False

        # exits
        isExitLong = (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit)
        isExitShort = (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit)

        ################################################################################################################

        if (isEntryLong):
            self.buy()
        elif (isEntryShort):
            self.sell()
        elif (isExitLong):
            self.position.close()
        elif (isExitShort):
            self.position.close()