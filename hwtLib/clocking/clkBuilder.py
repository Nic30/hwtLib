from hwt.code import If, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.defs import BIT
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.param import evalParam
from hwtLib.clocking.timers import TimerInfo, DynamicTimerInfo


class ClkBuilder(object):
    """
    :ivar compId: last component id used to avoid name collisions
    :ivar parent: unit in which will be all units created by this builder instanciated
    :ivar name: prefix for all instantiated units
    :ivar end: interface where builder endend
    """
    def __init__(self, parent, srcInterface, name=None):
        """
        :param parent: unit in which will be all units created by this builder instanciated
        :param name: prefix for all instantiated units
        :param srcInterface: input clock
        """
        self.parent = parent
        self.end = srcInterface
        if name is None:
            name = "gen_" + getSignalName(srcInterface)

        self.name = name
        self.compId = 0

    def timers(self, periods, enableSig=None, rstSig=None):
        """
        generate counters specified by count of iterations

        :param periods: list of integers/params which specifies periods of timers
            or tuple (name, integers/params)
        :param enableSig: enable signal for all counters
        :param rstSig: reset signal for all counters
        :attention: if tick of timer his high and enable Sig falls low tick will stay high

        :return: list of tick signals from timers
        """
        timers = []
        for p in periods:
            if isinstance(p, (tuple, list)):
                name, period = p
            else:
                name = None
                period = p

            t = TimerInfo(period, name=name)
            timers.append(t)

        TimerInfo.resolveSharing(timers)
        TimerInfo.instantiate(self.parent, timers, enableSig=enableSig, rstSig=rstSig)

        return list(map(lambda timer: timer.tick, timers))

    def timer(self, period, enableSig=None, rstSig=None):
        """
        Same as timers, just for one
        """
        return self.timers([period, ], enableSig=enableSig, rstSig=rstSig)[0]

    def timerDynamic(self, periodSig, enableSig=None, rstSig=None):
        """
        Same as timer, just period is signal which can be configured dynamically
        """
        if isinstance(periodSig, (tuple, list)):
            periodSig, name = periodSig
        else:
            periodSig, name = periodSig, getSignalName(periodSig)

        parentUnit = self.parent

        timer = DynamicTimerInfo(periodSig, name)
        maxVal = timer.maxVal - 1
        origMaxVal = timer.maxValOriginal - 1  # use original to propagate parameter
        assert maxVal._dtype.bit_length() > 0

        r = parentUnit._reg(timer.name + "_delayCntr",
                            periodSig._dtype,
                            )
        timer.cntrRegister = r
        tick = DynamicTimerInfo._instantiateTimerTickLogic(timer, origMaxVal, enableSig, rstSig)

        timer.tick = parentUnit._sig(timer.name + "_delayTick")
        timer.tick ** tick
        return timer.tick

    def oversample(self, sig, sampleCount, sampleTick, rstSig=None):
        """
        [TODO] last sample is not sampled correctly

        :param sig: signal to oversample
        :param sampleCount: count of samples to do
        :param sampleTick: signal to enable next sample taking
        :param rstSig: rstSig signal to reset internal counter, if is None it is not used
        """
        if sig._dtype != BIT:
            raise NotImplementedError()

        n = getSignalName(sig)

        sCnt = evalParam(sampleCount).val
        sampleDoneTick = self.timer((n + "_oversampleDoneTick", sampleCount),
                                    enableSig=sampleTick,
                                    rstSig=rstSig)
        oversampleCntr = self.parent._reg(n + "_oversample%d_cntr" % (sCnt),
                                          vecT(log2ceil(sampleCount) + 1, False),
                                          defVal=0)

        if rstSig is None:
            rstSig = sampleDoneTick
        else:
            rstSig = rstSig | sampleDoneTick

        If(sampleDoneTick,
            oversampleCntr ** 0
        ).Elif(sampleTick & sig,
            oversampleCntr ** (oversampleCntr + 1)
        )

        oversampled = self.parent._sig(n + "_oversampled%d" % (sCnt))
        oversampled ** (oversampleCntr > (sampleCount // 2 - 1))
        return oversampled, sampleDoneTick
