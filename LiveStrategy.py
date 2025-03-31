import numpy as np
import pandas as pd
from backtesting import Strategy

def ema(prices, bars, smoothing):
    raw = (pd.DataFrame(prices)
        .rolling(
            window=bars,
            win_type='exponential')
        .mean())
    smooth = (raw
        .rolling(
            window=smoothing,
            win_type='exponential')
        .mean())
    return np.array(smooth, dtype='float64')

def initArray(prices):
    return np.array(prices)

def getSlope(prices, bars, smoothing):
    exp = ema(prices, bars, smoothing)
    normalized = ((exp - exp[-1]) / exp) * 100
    slope = np.rad2deg(np.arctan(normalized))
    return slope

class LiveStrategy(Strategy):

    # optimization params
    fastMinutes = 25
    disableEntryMinutes = 0
    fastMomentumMinutes = 90
    fastCrossoverPercent = float(0)
    takeProfitPercent = float(0.32)
    fastAngle = float(40) # todo factor ...
    slowMinutes = 1555
    slowAngle = float(10)

    coolOffMinutes = 5
    positionEntryMinutes = 1

    # convert
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

        self.isExitLongFastCrossoverEnabled = False
        self.isExitShortFastCrossoverEnabled = False
        self.isExitLong = False
        self.isExitShort = False

        self.longEntryBarIndex = 0
        self.shortEntryBarIndex = 0
        self.longExitBarIndex = 0
        self.shortExitBarIndex = 0

        self.longTakeProfit = 0.0
        self.shortTakeProfit = 0.0
        self.longFastCrossoverExit = 0.0
        self.shortFastCrossoverExit = 0.0
        self.longFastCrossoverExit = 0.0
        self.shortFastCrossoverExit = 0.0


    def next(self):
        super().next()

        bar_index = len(self.data) - 1
        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        position = self.position
        is_long = self.position.is_long
        is_short = self.position.is_short

        disableEntryMinutes = self.disableEntryMinutes
        positionEntryMinutes = self.positionEntryMinutes
        coolOffMinutes = self.coolOffMinutes
        slowAngle = self.slowAngle
        fastCrossover = self.fastCrossover
        fastMomentumMinutes = self.fastMomentumMinutes
        fastAngle = self.fastAngle
        takeProfit = self.takeProfit

        fast = self.fast
        fastSlope = self.fastSlope
        slowSlope = self.slowSlope

        longEntryBarIndex = self.longEntryBarIndex
        shortEntryBarIndex = self.shortEntryBarIndex
        longFastCrossoverExit = self.longFastCrossoverExit
        shortFastCrossoverExit = self.shortFastCrossoverExit
        isExitLongFastCrossoverEnabled = self.isExitLongFastCrossoverEnabled
        isExitShortFastCrossoverEnabled = self.isExitShortFastCrossoverEnabled
        isExitLong = self.isExitLong
        isExitShort = self.isExitShort
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit

        # price crosses through fast average in favorable direction
        isFastCrossoverLong = (
            fastSlope[-1] > fastAngle
            and (fast[-1] > open[-1] or fast[-1] > close[-2])
            and high[-1] > fast[-1])[-1]
        isFastCrossoverShort = (
            -fastAngle > fastSlope[-1]
            and (open[-1] > fast[-1] or close[-2] > fast[-1])
            and fast[-1] > low[-1])[-1]

        # placeholder
        isEntryDisabled = False

        # allow entry only during starting minutes of trend
        isEntryLongDisabled = (
            False if disableEntryMinutes == 0 else
            True if np.min(fastSlope[-disableEntryMinutes:]) > 0 else
            False)
        isEntryShortDisabled = (
            False if disableEntryMinutes == 0 else
            True if 0 > np.max(fastSlope[-disableEntryMinutes:]) else
            False)

        # handle small volatility: 1-5 bars
        isEntryLongEnabled = (
            True if positionEntryMinutes == 0 else
            True if fast[-1] > np.max(open[-positionEntryMinutes:]) else
            False)
        isEntryShortEnabled = (
            True if positionEntryMinutes == 0 else
            True if np.min(open[-positionEntryMinutes:]) > fast[-1] else
            False)

        # cooloff time
        hasLongEntryDelayElapsed = bar_index - self.longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - self.shortExitBarIndex > coolOffMinutes

        # entries
        isEntryLong = (
            position.size == 0
            and slowSlope[-1] > slowAngle
            and isFastCrossoverLong
            and not isEntryDisabled
            and not isEntryLongDisabled
            and isEntryLongEnabled
            and hasLongEntryDelayElapsed)
        isEntryShort = (
            position.size == 0
            and -slowAngle > slowSlope[-1]
            and isFastCrossoverShort
            and not isEntryDisabled
            and not isEntryShortDisabled
            and isEntryShortEnabled
            and hasShortEntryDelayElapsed)

        # track entry
        self.longEntryBarIndex = bar_index if isEntryLong else longEntryBarIndex
        self.shortEntryBarIndex = bar_index if isEntryShort else shortEntryBarIndex

        # exit crossing back into fast in unfavorable direction
        self.longFastCrossoverExit = (
            None if fastCrossover == 0 else
            (1 + fastCrossover) * fast[-1] if isEntryLong else
            longFastCrossoverExit if is_long else
            None)

        self.shortFastCrossoverExit = (
            None if fastCrossover == 0 else
            (1 - fastCrossover) * fast[-1] if isEntryShort else
            shortFastCrossoverExit if is_short else
            None)

        self.isExitLongFastCrossoverEnabled = (
            False if self.longFastCrossoverExit is None else
            False if self.isExitLong else
            True if isExitLongFastCrossoverEnabled else
            True if is_long and high[-1] > self.longFastCrossoverExit
            else False)

        self.isExitShortFastCrossoverEnabled = (
            False if self.shortFastCrossoverExit is None else
            False if self.isExitShort else
            True if isExitShortFastCrossoverEnabled else
            True if is_short and self.shortFastCrossoverExit > low[-1] else False)

        isExitLongFastCrossover = (
            True if self.isExitLongFastCrossoverEnabled
                and is_long
                and fast[-1] > low[-1] else
            False)
        isExitShortFastCrossover = (
            True if self.isExitShortFastCrossoverEnabled
                and is_short
                and high[-1] > fast[-1] else
            False)

        # exit due to excessive momentum in unfavorable direction
        isExitLongFastMomentum = True if (
            fastMomentumMinutes != 0
            and is_long
            and -fastAngle > np.max(fastSlope[-fastMomentumMinutes:])) else False
        isExitShortFastMomentum = True if (
            fastMomentumMinutes != 0
            and is_short
            and np.min(fastSlope[-fastMomentumMinutes:]) > fastAngle) else False

        # take profit
        self.longTakeProfit = (
            longTakeProfit if is_long else
            (1 + takeProfit) * fast[-1] if isEntryLong and takeProfit != 0 else None)
        self.shortTakeProfit = (
            shortTakeProfit if is_short else
            (1 - takeProfit) * fast[-1] if isEntryShort and takeProfit != 0 else None)

        isExitLongTakeProfit = True if is_long and high[-1] > self.longTakeProfit else False
        isExitShortTakeProfit = True if is_short and self.shortTakeProfit > low[-1] else False

        # exits
        self.isExitLong = (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit) # todo refactor is_long and is_short go here
        self.isExitShort = (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit)

        # track exit
        self.longExitBarIndex = bar_index if self.isExitLong else self.longExitBarIndex
        self.shortExitBarIndex = bar_index if self.isExitShort else self.shortExitBarIndex

        ################################################################################################################

        # execute orders on framework
        if isEntryLong:
            self.buy()
        if isEntryShort:
            self.sell()
        if isExitLong or isExitShort:
            self.position.close()
