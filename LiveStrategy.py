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

        rawFast = self.data.Open
        rawSlow = self.data.Open
        fast = self.data.Open
        slow = self.data.Open
        entryPrice = self.data.Open
        longFastCrossoverExit = self.data.Open
        shortFastCrossoverExit = self.data.Open
        longTakeProfit = self.data.Open
        shortTakeProfit = self.data.Open

        fastAngle = self.fastAngleFactor / 1000.0
        slowAngle = self.slowAngleFactor / 1000.0
        takeProfit = self.takeProfitPercent / 100.0

        fastCrossover = (self.fastCrossoverPercent / 100.0) * takeProfit
        if (takeProfit == 0):
            fastCrossover = self.fastCrossoverPercent / 100.0

    def next(self):

