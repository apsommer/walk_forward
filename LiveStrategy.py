import numpy as np
import pandas as pd
from backtesting import Strategy

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

    def init(self):

        self.fastAngle = self.fastAngleFactor / 1000.0
        self.slowAngle = self.slowAngleFactor / 1000.0
        self.takeProfit = self.takeProfitPercent / 100.0

        self.fastCrossover = (self.fastCrossoverPercent / 100.0) * self.takeProfit
        if self.takeProfit == 0:
            self.fastCrossover = self.fastCrossoverPercent / 100.0

    def next(self):

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        rawFast = pd.Series(open).rolling(window=self.fastMinutes, win_type='exponential')
        rawSlow = pd.Series(open).rolling(window=self.slowMinutes, win_type='exponential')
        fast = rawFast.rolling(window=5, win_type='exponential')
        slow = rawSlow.rolling(window=200, win_type='exponential')

        normalizedFastPrice = ((fast - fast[-1]) / fast[-1]) * 100
        normalizedSlowPrice = ((slow - slow[-1]) / slow[-1]) * 100
        fastSlope = np.rad2deg(np.arctan(normalizedFastPrice))
        slowSlope = np.rad2deg(np.arctan(normalizedSlowPrice))

        # price crosses through fast average in favorable direction
        isFastCrossoverLong = (
            (fastSlope > self.fastAngle
            and (fast > open or fast > close[-1]))
            and high > fast)
        isFastCrossoverShort = (
            (-self.fastAngle > fastSlope
            and (open > fast or close[-1] > fast))
            and fast > low)

        # allow entry only during starting minutes of trend
        if (np.min(fastSlope, self.disableEntryMinutes) > 0
            and self.disableEntryMinutes != 0):
                self.isEntryLongDisabled = True
        if (0 > np.max(fastSlope, self.disableEntryMinutes)
            and self.disableEntryMinutes != 0):
                self.isEntryShortDisabled = True

        # handle short volatility todo can remove or simplify?
        if (fast > np.max(open, self.positionEntryMinutes) or self.positionEntryMinutes == 0):
            self.isEntryLongEnabled = True
        if (np.min(open, self.positionEntryMinutes) > fast or self.positionEntryMinutes == 0):
            self.isEntryShortEnabled = True

        # todo cooloff time

        # todo entry restriction idea

        # entries
        isEntryLong = (
            self.position == 0
           and isFastCrossoverLong
           and not self.isEntryLongDisabled
           and self.isEntryLongEnabled
           and slowSlope > self.slowAngle)
        isEntryShort = (
            self.position.size == 0
            and isFastCrossoverShort
            and not self.isEntryShortDisabled
            and self.isEntryShortEnabled
            and -self.slowAngle > slowSlope)

        # exit crossing back into fast in unfavorable direction
        longFastCrossoverExit = None
        if (self.fastCrossover == 0):
            longFastCrossoverExit = None
        elif (isEntryLong):
            longFastCrossoverExit = (1 + self.fastCrossover) * fast
        elif (self.position.is_long):
            longFastCrossoverExit = longFastCrossoverExit[-1]

        shortFastCrossoverExit = None
        if (self.fastCrossover == 0):
            shortFastCrossoverExit = None
        elif (isEntryShort):
            shortFastCrossoverExit = (1 - self.fastCrossover) * fast
        elif (self.position.is_short):
            shortFastCrossoverExit = shortFastCrossoverExit[-1]

        # todo omit isExitLong[1] condition as the array does not exist yet
        isExitLongFastCrossoverEnabled = False
        if (isExitLongFastCrossoverEnabled[-1]):
            isExitLongFastCrossoverEnabled = True
        elif self.position.is_long and high > longFastCrossoverExit:
            isExitLongFastCrossoverEnabled = False

        isExitShortFastCrossoverEnabled = False
        if (isExitShortFastCrossoverEnabled[-1]):
            isExitShortFastCrossoverEnabled = True
        elif self.position.is_short and shortFastCrossoverExit > low:
            isExitShortFastCrossoverEnabled = False

        isExitLongFastCrossover = True if (
            isExitLongFastCrossoverEnabled
            and self.position.is_long
            and fast > low) else False

        isExitShortFastCrossover = True if (
            isExitShortFastCrossoverEnabled
            and self.position.is_short
            and high > fast) else False

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = True if (
                self.fastMomentumMinutes != 0
                and self.position.is_long
                and -self.fastAngle > np.max(fastSlope, self.fastMomentumMinutes)) else False

        isExitShortFastMomentum = True if (
            self.fastMomentumMinutes != 0
            and self.position.is_short
            and np.min(fastSlope, self.fastMomentumMinutes) > self.fastAngle) else False

        # take profit
        longTakeProfit = None
        if (self.position.is_long):
            longTakeProfit = longTakeProfit[-1]
        elif (isEntryLong and self.takeProfit != 0):
            longTakeProfit = (1 +self.takeProfit) * fast

        shortTakeProfit = None
        if (self.position.is_short):
            shortTakeProfit = shortTakeProfit[-1]
        elif (isEntryShort and self.takeProfit != 0):
            shortTakeProfit = (1 - self.takeProfit) * fast

        isExitLongTakeProfit = True if (
            self.position.is_long
            and high > longTakeProfit
        ) else False

        isExitShortTakeProfit = True if (
            self.position.is_short
            and shortTakeProfit > low
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
            self.sell()
        elif (isExitShort):
            self.buy()