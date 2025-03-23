import numpy as np
import pandas as pd
from backtesting import Strategy
from decimal import Decimal, getcontext

getcontext().prec = 10

def ema(prices, bars, smooth):
    raw = pd.DataFrame(prices).rolling(window=bars, win_type='exponential').mean()
    smooth = raw.rolling(window=smooth, win_type='exponential').mean()
    return np.array(smooth)

def initArray(prices):
    return np.array(prices)

def getSlope(prices, bars, smooth):
    res = ema(prices, bars, smooth)
    diff = res - res[-1]
    pdiff = (diff / res[-1]) * 100
    slope = np.rad2deg(np.arctan(pdiff))
    return slope

class LiveStrategy(Strategy):

    # optimization params
    fastMinutes = 25
    disableEntryMinutes = 0
    fastMomentumMinutes = 110.0
    fastCrossoverPercent = 0.40
    takeProfitPercent = 0.0
    fastAngleFactor = 20.0
    slowMinutes = 1555
    slowAngleFactor = 20.0
    entryRestrictionMinutes = 15.0
    entryRestrictionPercent = 0.0

    coolOffMinutes = 5
    positionEntryMinutes = 1

    fastAngle = fastAngleFactor / 1000.0
    slowAngle = slowAngleFactor / 1000.0
    takeProfit = takeProfitPercent / 100.0

    fastCrossover = (fastCrossoverPercent / 100.0) * takeProfit
    if takeProfit == 0:
        fastCrossover = fastCrossoverPercent / 100.0

    def init(self):

        self.open = self.data.Open
        self.high = self.data.High
        self.low = self.data.Low
        self.close = self.data.Close
        self.ohlc4 = (self.open + self.high + self.low + self.close) / 4

        # exponential moving average
        self.fast = self.I(ema, self.ohlc4, self.fastMinutes, 5)
        self.slow = self.I(ema, self.ohlc4, self.slowMinutes, 200)
        self.fastSlope = self.I(getSlope, self.ohlc4, self.fastMinutes, 5)
        self.slowSlope = self.I(getSlope, self.ohlc4, self.slowMinutes, 200)

        # horizontal price lines
        self.longFastCrossoverExit = self.I(initArray, self.ohlc4)
        self.shortFastCrossoverExit = self.I(initArray, self.ohlc4)
        self.longTakeProfit = self.I(initArray, self.ohlc4)
        self.shortTakeProfit = self.I(initArray, self.ohlc4)

    def next(self):

        open = self.open
        high = self.high
        low = self.low
        close = self.close
        ohlc4 = self.ohlc4

        # disableEntryMinutes = self.disableEntryMinutes
        slowAngle = self.slowAngle
        position = self.position
        is_long = self.position.is_long
        is_short = self.position.is_short
        fastCrossover = self.fastCrossover
        fastMomentumMinutes = self.fastMomentumMinutes
        fastAngle = self.fastAngle
        takeProfit = self.takeProfit
        fast = self.fast
        # slow = self.slow
        fastSlope = self.fastSlope
        slowSlope = self.slowSlope

        # price crosses through fast average in favorable direction
        isFastCrossoverLong = (
            (fastSlope[0] > fastAngle
            and (fast[0] > open[0] or fast[0] > close[-1]))
            and high[0] > fast[0])
        isFastCrossoverShort = (
            (-fastAngle > fastSlope[0]
            and (open[0] > fast[0] or close[-1] > fast[0]))
            and fast[0] > low[0])

        # allow entry only during starting minutes of trend
        # if disableEntryMinutes == 0:
        #     isEntryLongDisabled = False
        #     isEntryShortDisabled = False
        # else:
        #     isEntryLongDisabled = True if np.min(fastSlope, disableEntryMinutes) > 0 else False
        #     isEntryShortDisabled = True if 0 > np.max(fastSlope, disableEntryMinutes) else False

        # todo handle short volatility

        # todo cooloff time

        # todo entry restriction idea

        # entries
        isEntryLong = (
            position == 0
            and isFastCrossoverLong
            # and not isEntryLongDisabled
            and slowSlope > slowAngle)
        isEntryShort = (
            position == 0
            and isFastCrossoverShort
            # and not isEntryShortDisabled
            and -slowAngle > slowSlope)

        # exit crossing back into fast in unfavorable direction
        if is_long:
            self.longFastCrossoverExit = self.longFastCrossoverExit[-1]
        if isEntryLong:
            self.longFastCrossoverExit = (1 + fastCrossover) * fast
        if is_short:
            self.shortFastCrossoverExit = self.shortFastCrossoverExit[-1]
        if isEntryShort:
            self.shortFastCrossoverExit = (1 - fastCrossover) * fast

        isExitLongFastCrossoverEnabled = True if is_long and high > self.longFastCrossoverExit else False
        isExitShortFastCrossoverEnabled = True if is_short and self.shortFastCrossoverExit > low else False

        isExitLongFastCrossover = True if (
            isExitLongFastCrossoverEnabled
            and is_long
            and fast > self.data.Low) else False

        isExitShortFastCrossover = True if (
            isExitShortFastCrossoverEnabled
            and is_short
            and self.data.High > fast) else False

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = True if (
                fastMomentumMinutes != 0
                and is_long
                and -fastAngle > fastSlope) else False

        isExitShortFastMomentum = True if (
            fastMomentumMinutes != 0
            and is_short
            and fastSlope > fastAngle) else False

        # take profit
        if is_long:
            self.longTakeProfit = self.longTakeProfit[-1]
        elif isEntryLong and self.takeProfit != 0:
            self.longTakeProfit = (1 + takeProfit) * fast

        if is_short:
            self.shortTakeProfit = self.shortTakeProfit[-1]
        elif isEntryShort and takeProfit != 0:
            self.shortTakeProfit = (1 - takeProfit) * fast

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
