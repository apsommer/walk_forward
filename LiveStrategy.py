import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.test import SMA

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

    #############################################

    fastAngle = fastAngleFactor / 1000.0
    slowAngle = slowAngleFactor / 1000.0
    takeProfit = takeProfitPercent / 100.0

    fastCrossover = (fastCrossoverPercent / 100.0) * takeProfit
    if (takeProfit == 0):
        fastCrossover = fastCrossoverPercent / 100.0

    def init(self):

        isStrategyEnabled = False
        strategyStartIndex = 0
        fastSlope = 0.0
        slowSlope = 0.0
        slowPositiveBarIndex = 0
        slowNegativeBarIndex = 0
        isFastCrossoverLong = False
        isFastCrossoverShort = False
        isEntryDisabled = False
        isEntryLongDisabled = False
        isEntryShortDisabled = False
        hasLongEntryDelayElapsed = False
        hasShortEntryDelayElapsed = False
        isEntryLongEnabled = False
        isEntryShortEnabled = False
        isEntryLong = False
        isEntryShort = False
        isEntryLongPyramid = False
        isEntryShortPyramid = False
        isExitLongFastCrossoverEnabled = False
        isExitShortFastCrossoverEnabled = False
        isExitLongFastCrossover = False
        isExitShortFastCrossover = False
        isExitLongFastMomentum = False
        isExitShortFastMomentum = False
        isExitLongTakeProfit = False
        isExitShortTakeProfit = False
        isExitLong = False
        isExitShort = False
        longExitBarIndex = 0
        shortExitBarIndex = 0
        position = 0
        quantity = 0

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

        isFastCrossoverLong = ((fastSlope > self.fastAngle and
                               (fast > open or fast > close[1])) and
                               high > fast)

        isFastCrossoverShort = ((-self.fastAngle > fastSlope and
                                (open > fast or close[1] > fast)) and
                                fast > low)

        # allow entry at start of trend only
        if (np.min(fastSlope, self.disableEntryMinutes) > 0 and self.disableEntryMinutes != 0):
            self.isEntryLongDisabled = True
        if (0 > np.max(fastSlope, self.disableEntryMinutes) and self.disableEntryMinutes != 0):
            self.isEntryShortDisabled = True

        # handle short volatility
        if (fast > np.max(open, self.positionEntryMinutes) or self.positionEntryMinutes == 0):
            self.isEntryLongEnabled = True
        if (np.min(open, self.positionEntryMinutes) > fast or self.positionEntryMinutes == 0):
            self.isEntryShortEnabled = True

        # todo cooloff time

        # todo entry restriction idea

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
