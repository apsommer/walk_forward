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
    disableEntryMinutes = 180
    fastMomentumMinutes = 110
    fastCrossoverPercent = 80
    takeProfitPercent = 0.5
    fastAngleFactor = 20.0
    slowMinutes = 1555
    slowAngleFactor = 20.0
    entryRestrictionMinutes = 0
    entryRestrictionPercent = 0.0

    coolOffMinutes = 5
    positionEntryMinutes = 1

    # convert
    fastAngle = fastAngleFactor / 1000.0
    slowAngle = slowAngleFactor / 1000.0
    takeProfit = takeProfitPercent / 100.0
    fastCrossover = fastCrossoverPercent / 100.0 if takeProfit == 0 else (fastCrossoverPercent / 100.0) * takeProfit

    def init(self):
        super().init()

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        # fast and slow EMA
        ohlc4 = (open + high + low + close) / 4
        self.fast = self.I(ema, ohlc4, self.fastMinutes, 5)
        self.slow = self.I(ema, ohlc4, self.slowMinutes, 200)
        self.fastSlope = self.I(getSlope, ohlc4, self.fastMinutes, 5)
        self.slowSlope = self.I(getSlope, ohlc4, self.slowMinutes, 200)

        self.longFastCrossoverExit = None
        self.shortFastCrossoverExit = None
        self.longExitBarIndex = 0
        self.shortExitBarIndex = 0
        self.isExitLongFastCrossoverEnabled = False
        self.isExitShortFastCrossoverEnabled = False
        self.longTakeProfit = None
        self.shortTakeProfit = None

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
            and (fast[-1] > open[-1] or fast[-1] > close[-1])
            and high[-1] > fast[-1])
        isFastCrossoverShort = (
            -fastAngle > fastSlope[-1]
            and (open[-1] > fast[-1] or close[-1] > fast[-1])
            and fast[-1] > low[-1])

        isEntryDisabled = False

        # allow entry only during starting minutes of trend
        isEntryLongDisabled = True if np.min(fastSlope[-self.disableEntryMinutes:]) > 0 else False
        isEntryShortDisabled = True if 0 > np.max(fastSlope[-self.disableEntryMinutes:]) else False

        # handle small volatility: 1-5 bars
        isEntryLongEnabled = True if fast[-1] > np.max(open[-self.positionEntryMinutes:]) else True if self.positionEntryMinutes == 0 else False
        isEntryShortEnabled = True if np.min(open[-self.positionEntryMinutes:]) > fast[-1] else True if self.positionEntryMinutes == 0 else False

        # cooloff time
        bar_index = len(self.data) - 1
        hasLongEntryDelayElapsed = bar_index - self.longExitBarIndex > self.coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - self.shortExitBarIndex > self.coolOffMinutes

        # todo entry restriction idea

        # entries
        isEntryLong = (
            position.size == 0
            and isFastCrossoverLong
            and not isEntryLongDisabled
            and isEntryLongEnabled
            and slowSlope[-1] > slowAngle
            and hasLongEntryDelayElapsed)
        isEntryShort = (
            position.size == 0
            and isFastCrossoverShort
            and not isEntryShortDisabled
            and isEntryShortEnabled
            and -slowAngle > slowSlope[-1]
            and hasShortEntryDelayElapsed)

        # exit crossing back into fast in unfavorable direction
        self.longFastCrossoverExit = self.longFastCrossoverExit if is_long else \
            (1 + fastCrossover) * fast[-1] if isEntryLong else None
        self.shortFastCrossoverExit = self.shortFastCrossoverExit if is_short else \
            (1 - fastCrossover) * fast[-1] if isEntryShort else None

        self.isExitLongFastCrossoverEnabled = \
            True if self.isExitLongFastCrossoverEnabled else \
                True if is_long and high[-1] > self.longFastCrossoverExit else False
        self.isExitShortFastCrossoverEnabled = \
            True if self.isExitShortFastCrossoverEnabled else \
                True if is_short and self.shortFastCrossoverExit > low[-1] else False

        isExitLongFastCrossover = \
            True if self.isExitLongFastCrossoverEnabled and is_long and fast[-1] > low[-1] else False
        isExitShortFastCrossover = \
            True if self.isExitShortFastCrossoverEnabled and is_short and high[-1] > fast[-1] else False

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = \
            True if fastMomentumMinutes != 0 and is_long and -fastAngle > fastSlope[-1] else False
        isExitShortFastMomentum = \
            True if fastMomentumMinutes != 0 and is_short and fastSlope[-1] > fastAngle else False

        # take profit
        self.longTakeProfit = \
            self.longTakeProfit if is_long else \
            (1 + takeProfit) * fast[-1] if isEntryLong and self.takeProfit != 0 else None
        self.shortTakeProfit = \
            self.shortTakeProfit if is_short else \
            (1 - takeProfit) * fast[-1] if isEntryShort and takeProfit != 0 else None
        isExitLongTakeProfit = \
            True if is_long and high[-1] > self.longTakeProfit else False
        isExitShortTakeProfit = \
            True if is_short and self.shortTakeProfit > low[-1] else False

        # exits
        isExitLong = (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit)
        isExitShort = (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit)

        # track exit
        self.longExitBarIndex = bar_index if isExitLong else self.longExitBarIndex
        self.shortExitBarIndex = bar_index if isExitShort else self.shortExitBarIndex

        ################################################################################################################

        # execute orders on framework
        self.buy() if isEntryLong else (
            self.sell()) if isEntryShort else (
            self.position.close()) if isExitLong else (
            self.position.close()) if isExitShort else None

