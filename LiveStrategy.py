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

    # constants
    fastAngle = fastAngleFactor / 1000.0
    slowAngle = slowAngleFactor / 1000.0
    takeProfit = takeProfitPercent / 100.0

    fastCrossover = (fastCrossoverPercent / 100.0) * takeProfit
    if takeProfit == 0:
        fastCrossover = fastCrossoverPercent / 100.0

    # todo ?
    # def init(self):

    def next(self):

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        rawFast = pd.Series(open).ewm(min_periods=self.fastMinutes)
        rawSlow = pd.Series(open).ewm(min_periods=self.slowMinutes)

        fast = rawFast.ewm(min_periods=5)
        slow = rawSlow.ewm(min_periods=200)
        normalizedFastPrice = ((fast - fast[1]) / fast) * 100 # todo should be / fast[1]
        normalizedSlowPrice = ((slow - slow[1]) / slow) * 100# todo should be / slow[1]
        fastSlope = np.rad2deg(np.arctan(normalizedFastPrice))
        slowSlope = np.rad2deg(np.arctan(normalizedSlowPrice))

        # price crosses through fast average in favorable direction
        isFastCrossoverLong = ((fastSlope > self.fastAngle and
                               (fast > open or fast > close[1])) and
                               high > fast)
        isFastCrossoverShort = ((-self.fastAngle > fastSlope and
                                (open > fast or close[1] > fast)) and
                                fast > low)

        # allow entry only during starting minutes of trend
        if (np.min(fastSlope, self.disableEntryMinutes) > 0 and self.disableEntryMinutes != 0):
            self.isEntryLongDisabled = True
        if (0 > np.max(fastSlope, self.disableEntryMinutes) and self.disableEntryMinutes != 0):
            self.isEntryShortDisabled = True

        # handle short volatility todo can remove or simplify?
        if (fast > np.max(open, self.positionEntryMinutes) or self.positionEntryMinutes == 0):
            self.isEntryLongEnabled = True
        if (np.min(open, self.positionEntryMinutes) > fast or self.positionEntryMinutes == 0):
            self.isEntryShortEnabled = True

        # todo cooloff time

        # todo entry restriction idea

        # entries
        isEntryLong = (self.position == 0
                       and isFastCrossoverLong
                       and not self.isEntryDisabled
                       and not self.isEntryLongDisabled
                       and self.isEntryLongEnabled
                       and slowSlope > self.slowAngle)
        isEntryShort = (self.position == 0
                         and isFastCrossoverShort
                         and not self.isEntryDisabled
                         and not self.isEntryShortDisabled
                         and self.isEntryShortEnabled
                         and -self.slowAngle > slowSlope)

        # exit crossing back into fast in unfavorable direction

        # exit due to excessive momentum in unfavorable direction

        # take profit

        # exits