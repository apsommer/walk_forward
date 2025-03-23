import numpy as np
import pandas as pd
from backtesting import Strategy

def fast(fastMinutes):
    rawFast = pd.DataFrame(open).rolling(window=fastMinutes, win_type='exponential').mean()
    return rawFast.rolling(window=5, win_type='exponential').mean()

def slow(slowMinutes):
    rawSlow = pd.DataFrame(open).rolling(window=slowMinutes, win_type='exponential').mean()
    return rawSlow.rolling(window=200, win_type='exponential').mean()

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

        self.fast = self.I(fast, self.fastMinutes)
        self.slow = self.I(slow, self.slowMinutes)

        self.fastSlope = self.I
        self.slowSlope = self.I

        self.isEntryLong = self.I
        self.isEntryShort = self.I

        self.longFastCrossoverExit = self.I
        self.shortFastCrossoverExit = self.I

        self.isExitLongFastCrossoverEnabled = self.I
        self.isExitShortFastCrossoverEnabled = self.I

        self.longTakeProfit = self.I
        self.shortTakeProfit = self.I

        self.isExitLong = self.I
        self.isExitShort = self.I

    def next(self):

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        # self.rawFast = pd.DataFrame(open).rolling(window=self.fastMinutes, win_type='exponential').mean()
        # self.fast = self.rawFast.rolling(window=5, win_type='exponential').mean()

        # self.rawSlow = pd.DataFrame(open).rolling(window=self.slowMinutes, win_type='exponential').mean()
        # self.slow = self.rawSlow.rolling(window=200, win_type='exponential').mean()

        normalizedFastPrice = ((self.fast - self.fast[-1]) / self.fast[-1]) * 100
        normalizedSlowPrice = ((self.slow - self.slow[-1]) / self.slow[-1]) * 100
        self.fastSlope = np.rad2deg(np.arctan(normalizedFastPrice))
        self.slowSlope = np.rad2deg(np.arctan(normalizedSlowPrice))

        # price crosses through fast average in favorable direction
        isFastCrossoverLong = (
            (self.fastSlope > self.fastAngle
            and (self.fast > open or self.fast > close[-1]))
            and high > self.fast)
        isFastCrossoverShort = (
            (-self.fastAngle > self.fastSlope
            and (open > self.fast or close[-1] > self.fast))
            and self.fast > low)

        # allow entry only during starting minutes of trend
        if (np.min(self.fastSlope, self.disableEntryMinutes) > 0
            and self.disableEntryMinutes != 0):
                self.isEntryLongDisabled = True
        if (0 > np.max(self.fastSlope, self.disableEntryMinutes)
            and self.disableEntryMinutes != 0):
                self.isEntryShortDisabled = True

        # handle short volatility todo can remove or simplify?
        if (self.fast > np.max(open, self.positionEntryMinutes) or self.positionEntryMinutes == 0):
            self.isEntryLongEnabled = True
        if (np.min(open, self.positionEntryMinutes) > self.fast or self.positionEntryMinutes == 0):
            self.isEntryShortEnabled = True

        # todo cooloff time

        # todo entry restriction idea

        # entries
        self.isEntryLong = (
            self.position == 0
            and isFastCrossoverLong
            and not self.isEntryLongDisabled
            and self.isEntryLongEnabled
            and self.slowSlope > self.slowAngle)
        self.isEntryShort = (
            self.position.size == 0
            and isFastCrossoverShort
            and not self.isEntryShortDisabled
            and self.isEntryShortEnabled
            and -self.slowAngle > self.slowSlope)

        # exit crossing back into fast in unfavorable direction
        if self.fastCrossover == 0:
            self.longFastCrossoverExit = None
        elif (self.isEntryLong):
            self.longFastCrossoverExit = (1 + self.fastCrossover) * self.fast
        elif self.position.is_long:
            self.longFastCrossoverExit = self.longFastCrossoverExit[-1]

        if self.fastCrossover == 0:
            self.shortFastCrossoverExit = None
        elif self.isEntryShort:
            self.shortFastCrossoverExit = (1 - self.fastCrossover) * self.fast
        elif self.position.is_short:
            self.shortFastCrossoverExit = self.shortFastCrossoverExit[-1]

        # todo omit isExitLong.iloc[-1] condition as the array does not exist yet
        if self.isExitLongFastCrossoverEnabled[-1]:
            self.isExitLongFastCrossoverEnabled = True
        elif self.position.is_long and high > self.longFastCrossoverExit:
            self.isExitLongFastCrossoverEnabled = False

        if (self.isExitShortFastCrossoverEnabled[-1]):
            self.isExitShortFastCrossoverEnabled = True
        elif self.position.is_short and self.shortFastCrossoverExit > low:
            self.isExitShortFastCrossoverEnabled = False

        isExitLongFastCrossover = True if (
            self.isExitLongFastCrossoverEnabled
            and self.position.is_long
            and self.fast > low) else False

        isExitShortFastCrossover = True if (
            self.isExitShortFastCrossoverEnabled
            and self.position.is_short
            and high > self.fast) else False

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = True if (
                self.fastMomentumMinutes != 0
                and self.position.is_long
                and -self.fastAngle > np.max(self.fastSlope, self.fastMomentumMinutes)) else False

        isExitShortFastMomentum = True if (
            self.fastMomentumMinutes != 0
            and self.position.is_short
            and np.min(self.fastSlope, self.fastMomentumMinutes) > self.fastAngle) else False

        # take profit
        if self.position.is_long:
            self.longTakeProfit = self.longTakeProfit[-1]
        elif self.isEntryLong and self.takeProfit != 0:
            self.longTakeProfit = (1 +self.takeProfit) * self.fast

        if self.position.is_short:
            self.shortTakeProfit = self.shortTakeProfit[-1]
        elif self.isEntryShort and self.takeProfit != 0:
            self.shortTakeProfit = (1 - self.takeProfit) * self.fast

        isExitLongTakeProfit = True if (
            self.position.is_long
            and high > self.longTakeProfit
        ) else False

        isExitShortTakeProfit = True if (
            self.position.is_short
            and self.shortTakeProfit > low
        ) else False

        # exits
        self.isExitLong = (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit)
        self.isExitShort = (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit)

        ################################################################################################################

        if (self.isEntryLong):
            self.buy()
        elif (self.isEntryShort):
            self.sell()
        elif (self.isExitLong):
            self.position.close()
        elif (self.isExitShort):
            self.position.close()