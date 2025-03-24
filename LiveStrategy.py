import numpy as np
import pandas as pd
from backtesting import Strategy

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
    fastMomentumMinutes = 110
    fastCrossoverPercent = 0.40
    takeProfitPercent = 0.0
    fastAngleFactor = 20.0
    slowMinutes = 1555
    slowAngleFactor = 20.0
    entryRestrictionMinutes = 15
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
        super().init()

        self.open = self.data.Open
        self.high = self.data.High
        self.low = self.data.Low
        self.close = self.data.Close
        self.ohlc4 = (self.open + self.high + self.low + self.close) / 4

        self.fast = self.I(ema, self.ohlc4, self.fastMinutes, 5)
        self.slow = self.I(ema, self.ohlc4, self.slowMinutes, 200)
        self.fastSlope = self.I(getSlope, self.ohlc4, self.fastMinutes, 5)
        self.slowSlope = self.I(getSlope, self.ohlc4, self.slowMinutes, 200)

        self.longFastCrossoverExit = None
        self.shortFastCrossoverExit = None

    def next(self):
        super().next()

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

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
            fastSlope[-1] > fastAngle
            and fast[-1] > open[-1])
            # and high[-1] > fast[-1])
        isFastCrossoverShort = (
            -fastAngle > fastSlope[-1]
            and open[-1] > fast[-1])
            # and fast[-1] > low[-1])

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
            position.size == 0
            and isFastCrossoverLong
            # and not isEntryLongDisabled
            and slowSlope[-1] > slowAngle)
        isEntryShort = (
            position.size == 0
            and isFastCrossoverShort
            # and not isEntryShortDisabled
            and -slowAngle > slowSlope[-1])

        # exit crossing back into fast in unfavorable direction
        self.longFastCrossoverExit = self.longFastCrossoverExit if is_long else (1 + fastCrossover) * fast[-1] if isEntryLong else None
        self.shortFastCrossoverExit = self.shortFastCrossoverExit if is_short else (1 - fastCrossover) * fast[-1] if isEntryShort else None

        isExitLongFastCrossover = True if (
                self.longFastCrossoverExit is not None
                and high[-1] > self.longFastCrossoverExit
                and is_long
                and fast[-1] > low[-1]) else False

        isExitShortFastCrossover = True if (
                self.shortFastCrossoverExit is not None
                and self.shortFastCrossoverExit > low[-1]
                and is_short
                and high[-1] > fast[-1]) else False

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = True if (
            fastMomentumMinutes != 0
            and is_long
            and -fastAngle > fastSlope[-1]) else False

        isExitShortFastMomentum = True if (
            fastMomentumMinutes != 0
            and is_short
            and fastSlope[-1] > fastAngle) else False

        # take profit
        # if is_long:
        #     self.longTakeProfit = self.longTakeProfit[-1]
        # elif isEntryLong and self.takeProfit != 0:
        #     self.longTakeProfit = (1 + takeProfit) * fast[-1]
        #
        # if is_short:
        #     self.shortTakeProfit = self.shortTakeProfit[-1]
        # elif isEntryShort and takeProfit != 0:
        #     self.shortTakeProfit = (1 - takeProfit) * fast[-1]
        #
        # isExitLongTakeProfit = True if (
        #     is_long
        #     and high > self.longTakeProfit
        # ) else False
        #
        # isExitShortTakeProfit = True if (
        #     is_short
        #     and self.shortTakeProfit > low
        # ) else False

        # exits
        isExitLong = (
            isExitLongFastCrossover
            or isExitLongFastMomentum)
            # or isExitLongTakeProfit)
        isExitShort = (
            isExitShortFastCrossover
            or isExitShortFastMomentum)
            # or isExitShortTakeProfit)

        ################################################################################################################

        if isEntryLong:
            self.buy()
        elif isEntryShort:
            self.sell()
        elif isExitLong:
            self.position.close()
        elif isExitShort:
            self.position.close()
