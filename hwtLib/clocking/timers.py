from hwt.code import log2ceil, If, isPow2
from hwt.hdl.types.bits import Bits
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from typing import Optional, Union
from hwt.synthesizer.unit import Unit
from hwt.hdl.value import Value


class TimerInfo(object):
    """
    Generator of varius shared timers

    :ivar cntrRegister: counter register for this timer
    :ivar tick: signal with tick from this timer
    :ivar parent: parent TimerInfo object from which this timer can be generated
    :ivar maxValOriginal: original value of maxVal
    :ivar maxVal: evaluated value of maxVal
    :ivar name: name prefix which is used for registers and signals for this timer
    """
    __slots__ = ['maxVal', 'maxValOriginal',
                 'parent', 'cntrRegister', 'tick', 'name']

    def __init__(self, maxVal, name=None):
        self.maxValOriginal = maxVal
        self.maxVal = int(maxVal)
        assert isinstance(self.maxVal, int), self.maxVal
        self.parent = None

        if name is None:
            self.name = ""
        else:
            self.name = name

    @staticmethod
    def resolveSharing(timers):
        # filter out timers with maxVal == 1 because they are only clock
        timers = sorted(where(timers,
                              lambda t: t.maxVal != 1),
                        key=lambda t: t.maxVal, reverse=True)
        for i, t in enumerate(timers):
            if isPow2(t.maxVal):
                # this timer will be driven from bit of some larger
                # counter if there is suitable
                for possibleParent in timers[:i]:
                    if possibleParent.maxVal % t.maxVal == 0:
                        if possibleParent.parent is not None:
                            continue
                        t.parent = possibleParent
                        break
            else:
                # this timer will have its own timer which will be enabled by
                # some other timer if there is suitable
                for possibleParent in timers[(i + 1):]:
                    if t.maxVal % possibleParent.maxVal == 0:
                        if possibleParent.parent is t:
                            continue
                        t.parent = possibleParent
                        break

    @staticmethod
    def _instantiateTimerWithParent(parentUnit, timer, parent, enableSig, rstSig):
        p = parent
        if not hasattr(p, "tick"):
            TimerInfo._instantiateTimer(parentUnit, p, enableSig, rstSig)
        assert hasattr(p, "tick")

        if p.maxVal == timer.maxVal:
            timer.cntrRegister = p.cntrRegister
            timer.tick = p.tick

        elif p.maxVal < timer.maxVal:
            maxVal = (timer.maxVal // p.maxVal) - 1
            assert maxVal >= 0
            timer.tick = parentUnit._sig(
                timer.name + "timerTick%d" % timer.maxVal)

            timer.cntrRegister = parentUnit._reg(
                timer.name + "timerCntr%d" % timer.maxVal,
                Bits(log2ceil(maxVal + 1)),
                maxVal
            )

            en = p.tick
            if enableSig is not None:
                en = en & enableSig

            tick = TimerInfo._instantiateTimerTickLogic(
                parentUnit,
                timer,
                (timer.maxValOriginal // p.maxValOriginal) - 1,
                en,
                rstSig)

            timer.tick(tick & p.tick)

        else:
            # take specific bit from wider counter
            assert isPow2(timer.maxVal), timer.maxVal
            bitIndx = log2ceil(timer.maxVal)

            timer.cntrRegister = p.cntrRegister

            timer.tick = p.cntrRegister[bitIndx:]._eq(0)
            if enableSig is not None:
                timer.tick = timer.tick & enableSig

    @staticmethod
    def _instantiateTimerTickLogic(parentUnit: Unit, timer: RtlSignal,
                                   origMaxVal: Union[int, RtlSignal, Value],
                                   enableSig: Optional[RtlSignal],
                                   rstSig: Optional[RtlSignal]) -> RtlSignal:
        """
        Instantiate logic of this timer

        :return: tick signal from this timer
        """
        r = timer.cntrRegister

        tick = r._eq(0)
        if enableSig is None:
            if rstSig is None:
                If(tick,
                    r(origMaxVal)
                   ).Else(
                    r(r - 1)
                )
            else:
                If(rstSig | tick,
                    r(origMaxVal)
                   ).Else(
                    r(r - 1)
                )
        else:
            if rstSig is None:
                If(enableSig,
                    If(tick,
                        r(origMaxVal)
                    ).Else(
                        r(r - 1)
                    )
                )
            else:
                If(rstSig | (enableSig & tick),
                    r(origMaxVal)
                ).Elif(enableSig,
                    r(r - 1)
                )

        if enableSig is not None:
            tick = (tick & enableSig)

        if rstSig is not None:
            tick = (tick & ~rstSig)

        if timer.name:
            # wrap tick in signal
            s = parentUnit._sig(timer.name)
            s(tick)
            tick = s

        return tick

    @staticmethod
    def _instantiateTimer(parentUnit, timer, enableSig=None, rstSig=None):
        """
        :param enableSig: enable signal for all counters
        :param rstSig: reset signal for all counters
        """

        if timer.parent is None:
            maxVal = timer.maxVal - 1
            # use original to propagate parameter
            origMaxVal = timer.maxValOriginal - 1
            assert maxVal >= 0

            if maxVal == 0:
                if enableSig is None:
                    tick = 1
                else:
                    tick = enableSig
            else:
                timer.cntrRegister = parentUnit._reg(
                    timer.name + "timerCntr%d" % timer.maxVal,
                    Bits(log2ceil(maxVal + 1)),
                    maxVal
                )
                tick = TimerInfo._instantiateTimerTickLogic(parentUnit,
                                                            timer,
                                                            origMaxVal,
                                                            enableSig,
                                                            rstSig)

            timer.tick = parentUnit._sig(
                timer.name + "timerTick%d" % timer.maxVal
            )
            timer.tick(tick)
        else:
            TimerInfo._instantiateTimerWithParent(
                parentUnit, timer,
                timer.parent, enableSig, rstSig)

    @staticmethod
    def instantiate(parentUnit, timers, enableSig=None, rstSig=None):
        """
        :param enableSig: enable signal for all counters
        :param rstSig: reset signal for all counters
        """
        for timer in timers:
            if not hasattr(timer, "tick"):
                TimerInfo._instantiateTimer(parentUnit, timer,
                                            enableSig=enableSig, rstSig=rstSig)

    def __repr__(self):
        return "<%s maxVal=%d>" % (self.__class__.__name__, self.maxVal)


class DynamicTimerInfo(TimerInfo):
    """
    Meta informations about timer with dynamic period
    """

    def __init__(self, maxVal, name=None):
        self.maxValOriginal = maxVal
        self.maxVal = maxVal
        self.parent = None

        if name is None:
            self.name = ""
        else:
            self.name = name

    @staticmethod
    def _instantiateTimerTickLogic(timer: RtlSignal,
                                   period: RtlSignal,
                                   enableSig: Optional[RtlSignal],
                                   rstSig: Optional[RtlSignal]):
        """
        Instantiate incrementing timer with optional reset and enable signal

        :param timer: timer main register
        :param period: signal with actual period
        :param enableSig: optional enable signal for this timer
        :param rstSig: optional reset signal for this timer
        """

        r = timer.cntrRegister
        tick = r._eq(period - 1)
        if enableSig is None:
            if rstSig is None:
                cond = tick
            else:
                cond = rstSig | tick,

            If(cond,
                r(0)
            ).Else(
                r(r + 0)
            )
        else:
            if rstSig is None:
                If(enableSig,
                    If(tick,
                        r(0)
                    ).Else(
                        r(r + 1)
                    )
                )
            else:
                If(rstSig | (enableSig & tick),
                    r(0)
                ).Elif(enableSig,
                    r(r + 1)
                )

        if enableSig is not None:
            tick = (tick & enableSig)

        if rstSig is not None:
            tick = (tick & ~rstSig)

        return tick
