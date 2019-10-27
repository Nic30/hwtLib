from hwt.code import If, log2ceil
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwtLib.clocking.timers import TimerInfo, DynamicTimerInfo
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from typing import Tuple


class ClkBuilder(object):
    """
    :ivar compId: last component id used to avoid name collisions
    :ivar parent: unit in which will be all units created by this builder instantiated
    :ivar name: prefix for all instantiated units
    :ivar end: interface where builder ended
    """
    def __init__(self, parent, srcInterface, name=None):
        """
        :param parent: unit in which will be all units created by this builder instantiated
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
            or tuple (name, integer/param)
        :param enableSig: enable signal for all counters
        :param rstSig: reset signal for all counters
        :attention: if tick of timer his high and enableSig falls low tick will stay high

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

    def timerDynamic(self, periodSig, enableSig=None, rstSig=None) -> RtlSignal:
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
        assert maxVal._dtype.bit_length() > 0

        r = parentUnit._reg(timer.name + "_delayCntr",
                            periodSig._dtype,
                            def_val=0
                            )
        timer.cntrRegister = r
        tick = DynamicTimerInfo._instantiateTimerTickLogic(timer,
                                                           periodSig,
                                                           enableSig,
                                                           rstSig)

        timer.tick = parentUnit._sig(timer.name + "_delayTick")
        timer.tick(tick)
        return timer.tick

    def oversample(self, sig, sampleCount, sampleTick, rstSig=None) -> Tuple[RtlSignal, RtlSignal]:
        """
        [TODO] last sample is not sampled correctly

        :param sig: signal to oversample
        :param sampleCount: count of samples to do
        :param sampleTick: signal to enable next sample taking
        :param rstSig: rstSig signal to reset internal counter, if is None it is not used

        :return: typle (oversampled signal, oversample valid signal) 
        """
        if sig._dtype != BIT:
            raise NotImplementedError()

        n = getSignalName(sig)

        sCnt = int(sampleCount)
        sampleDoneTick = self.timer((n + "_oversampleDoneTick", sampleCount),
                                    enableSig=sampleTick,
                                    rstSig=rstSig)
        oversampleCntr = self.parent._reg(n + "_oversample%d_cntr" % (sCnt),
                                          Bits(log2ceil(sampleCount) + 1, False),
                                          def_val=0)

        if rstSig is None:
            rstSig = sampleDoneTick
        else:
            rstSig = rstSig | sampleDoneTick

        If(sampleDoneTick,
            oversampleCntr(0)
        ).Elif(sampleTick & sig,
            oversampleCntr(oversampleCntr + 1)
        )

        oversampled = self.parent._sig(n + "_oversampled%d" % (sCnt))
        oversampled(oversampleCntr > (sampleCount // 2 - 1))
        return oversampled, sampleDoneTick

    def edgeDetector(self, sig, rise=False, fall=False, last=None, initVal=0):
        """
        :param sig: signal to detect edges on
        :param rise: if True signal for rise detecting will be returned
        :param fall: if True signal for fall detecting will be returned
        :param last: last value for sig (use f.e. when you have register and it's next signal (sig=reg.next, last=reg))
            if last is None last register will be automatically generated
        :param initVal: if last is None initVal will be used as its initialization value
        :return: signals which is high on on rising/falling edge or both (specified by rise, fall parameter)
        """
        namePrefix = getSignalName(sig)
        assert rise or fall
        if last is None:
            last = self.parent._reg(namePrefix + "_edgeDetect_last", def_val=initVal)
            last(sig)

        if rise:
            riseSig = self.parent._sig(namePrefix + "_rising")
            riseSig(sig & ~last)
        if fall:
            fallSig = self.parent._sig(namePrefix + "_falling")
            fallSig(~sig & last)
        if rise and not fall:
            return riseSig
        elif not rise and fall:
            return fallSig
        else:
            return (riseSig, fallSig)
