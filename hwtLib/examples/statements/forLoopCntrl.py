#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal, HandshakeSync
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class StaticForLoopCntrl(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ITERATIONS = Param(15)

    def _declr(self):
        addClkRstn(self)

        self.cntrl = HandshakeSync()

        self.COUNTER_WIDTH = log2ceil(self.ITERATIONS)
        self.index = VectSignal(self.COUNTER_WIDTH)._m()
        self.body = HandshakeSync()._m()
        self.bodyBreak = Signal()

    def _impl(self):
        ITERATIONS = int(self.ITERATIONS)
        """
        Iterates from ITERATIONS -1 to 0 body is enabled by bodyVld and if bodyRd
        then counter is decremented for next iteration
        break causes reset of counter
        """

        counter = self._reg("counter", Bits(self.COUNTER_WIDTH), ITERATIONS - 1)

        If(counter._eq(0),
            If(self.cntrl.vld,
               counter(ITERATIONS - 1)
            )
        ).Else(
            If(self.body.rd,
                If(self.bodyBreak,
                    counter(0)
                ).Else(
                    counter(counter - 1)
                )
            )
        )

        self.cntrl.rd(counter._eq(0))
        self.body.vld(counter != 0)
        self.index(counter[self.COUNTER_WIDTH:0])


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = StaticForLoopCntrl()
    print(to_rtl_str(u))
