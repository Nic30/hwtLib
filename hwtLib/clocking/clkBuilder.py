from typing import Tuple, Union, List

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.math import log2ceil
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.clocking.timers import TimerInfo, DynamicTimerInfo


AnySig = Union[RtlSignal, Interface]


class ClkBuilder(AbstractComponentBuilder):
    """
    Helper object which simplifies construction
    of the oversampling, shared timers, edge detector, ... logic

    :ivar ~.compId: last component id used to avoid name collisions
    :ivar ~.parent: unit in which will be all units created by this builder instantiated
    :ivar ~.name: prefix for all instantiated units
    :ivar ~.end: interface where builder ended
    """

    def timers(self, periods: List[Union[int, Tuple[str, int]]],
               enableSig=None, rstSig=None):
        """
        generate counters specified by count of iterations

        :param periods: list tick period or tuple (name, period) for timer,
            period is sepecified in the number of clk ticks
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
        TimerInfo.instantiate(
            self.parent, timers,
            enableSig=enableSig, rstSig=rstSig)

        return [timer.tick for timer in timers]

    def timer(self, period, enableSig=None, rstSig=None):
        """
        Same as :func:`.ClkBuilder.timers`, just for single timer intance
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
        oversampleCntr = self.parent._reg(f"{n:s}_oversample{sCnt:d}_cntr",
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

        oversampled = self.parent._sig(f"{n:s}_oversampled{sCnt:d}")
        oversampled(oversampleCntr > (sampleCount // 2 - 1))
        return oversampled, sampleDoneTick

    def edgeDetector(self, sig, rise=False, fall=False, last=None, initVal=0):
        """
        :param sig: signal to detect edges on
        :param rise: if True signal for rise detecting will be returned
        :param fall: if True signal for fall detecting will be returned
        :param last: last value for sig (use e.g. when you have register and it's next signal (sig=reg.next, last=reg))
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

    def reg_path(self, din, number_of_regs, name=None, def_val=None):
        """
        Instanciate path of registers used to delay the signal or to filter IO

        :return: the last register in path
        """
        if name is None:
            name = "reg_path"
        for i in range(number_of_regs):
            reg = self.parent._reg(f"{name:s}_{i:d}",
                                   dtype=din._dtype, def_val=def_val)
            reg(din)
            din = reg

        return din
