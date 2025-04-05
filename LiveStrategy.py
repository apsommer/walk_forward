import numpy as np
import pandas as pd
from backtesting import Strategy
import Repository as repo

def ema(prices, bars, smoothing):

    raw = (pd.DataFrame(prices).rolling(window=bars, win_type='exponential').mean())
    smooth = (raw.rolling(window=smoothing, win_type='exponential').mean())
    ema = np.array(smooth, dtype='float64')
    return ema

def slope(prices, bars, smoothing):

    exp = ema(prices, bars, smoothing)
    normalized = ((exp - exp[-1]) / exp) * 100
    slope = np.rad2deg(np.arctan(normalized))
    return slope

class LiveStrategy(Strategy):

    # optimization params
    fastMinutes = 25
    disableEntryMinutes = 0
    fastMomentumMinutes = 90
    fastCrossoverPercent = float(80)
    takeProfitPercent = float(0.5)
    fastAngleFactor = float(40)
    slowMinutes = 1555
    slowAngleFactor = float(10)

    coolOffMinutes = 5
    positionEntryMinutes = 1

    # convert
    takeProfit = takeProfitPercent / 100.0
    fastCrossover = (
        fastCrossoverPercent / 100.0 if takeProfit == 0 else
        (fastCrossoverPercent / 100.0) * takeProfit)
    fastAngle = fastAngleFactor / 1000.0
    slowAngle = slowAngleFactor / 1000.0

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)

        self.shortFastCrossoverExit = None
        self.longFastCrossoverExit = None
        self.shortTakeProfit = None
        self.longTakeProfit = None
        self.shortExitBarIndex = None
        self.longExitBarIndex = None
        self.shortEntryBarIndex = None
        self.longEntryBarIndex = None
        self.isExitShort = None
        self.barIndex = None
        self.isExitLong = None
        self.isExitShortFastCrossoverEnabled = None
        self.isExitLongFastCrossoverEnabled = None
        self.slowSlope = None
        self.fastSlope = None
        self.slow = None
        self.fast = None

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
        self.fastSlope = self.I(slope, ohlc4, self.fastMinutes, 5)
        self.slowSlope = self.I(slope, ohlc4, self.slowMinutes, 200)

        self.isExitLongFastCrossoverEnabled = False
        self.isExitShortFastCrossoverEnabled = False
        self.isExitLong = False
        self.isExitShort = False

        self.barIndex = -1
        self.longEntryBarIndex = -1
        self.shortEntryBarIndex = -1
        self.longExitBarIndex = -1
        self.shortExitBarIndex = -1

        self.longTakeProfit = 0.0
        self.shortTakeProfit = 0.0
        self.longFastCrossoverExit = 0.0
        self.shortFastCrossoverExit = 0.0
        self.longFastCrossoverExit = 0.0
        self.shortFastCrossoverExit = 0.0

    def next(self):
        super().next()

        self.barIndex += 1
        barIndex = self.barIndex

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
        fastAngle = self.fastAngle
        slowAngle = self.slowAngle
        fastCrossover = self.fastCrossover
        fastMomentumMinutes = self.fastMomentumMinutes
        takeProfit = self.takeProfit

        fast = self.fast
        fastSlope = self.fastSlope
        slowSlope = self.slowSlope

        longEntryBarIndex = self.longEntryBarIndex
        shortEntryBarIndex = self.shortEntryBarIndex
        longExitBarIndex = self.longExitBarIndex
        shortExitBarIndex = self.shortExitBarIndex

        longFastCrossoverExit = self.longFastCrossoverExit
        shortFastCrossoverExit = self.shortFastCrossoverExit
        isExitLongFastCrossoverEnabled = self.isExitLongFastCrossoverEnabled
        isExitShortFastCrossoverEnabled = self.isExitShortFastCrossoverEnabled
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
        hasLongEntryDelayElapsed = barIndex - longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = barIndex - shortExitBarIndex > coolOffMinutes

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
        self.longEntryBarIndex = barIndex if isEntryLong else longEntryBarIndex
        self.shortEntryBarIndex = barIndex if isEntryShort else shortEntryBarIndex

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
        self.longExitBarIndex = barIndex if self.isExitLong else longExitBarIndex
        self.shortExitBarIndex = barIndex if self.isExitShort else shortExitBarIndex

        ################################################################################################################

        # execute orders on framework
        if isEntryLong:
            self.buy()
        if isEntryShort:
            self.sell()
        if self.isExitLong or self.isExitShort:
            self.position.close()

        if barIndex == 10221:
            repo.logm(self)

    def __str__(self):
        return (
            "\n\n" + "fastAngle: " + str(self.fastAngle) + "\n"
            "barIndex: " + str(self.barIndex) + "\n" +
            "longEntryBarIndex: " + str(self.longEntryBarIndex) + "\n" +
            "shortEntryBarIndex: " + str(self.shortEntryBarIndex) + "\n" +
            "\n" +
            "fast: " + str(self.fast[-1]) + "\n" +
            "slow: " + str(self.slow[-1]) + "\n" +
            "longFastCrossoverExit: " + str(self.longFastCrossoverExit) + "\n"
            "longTakeProfit: " + str(self.longTakeProfit) + "\n"
        )