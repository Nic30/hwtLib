#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal, HwIORdVldSync
from hwt.hwIOs.utils import addClkRstn
from hwt.math import log2ceil
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule


class StaticForLoopCntrl(HwModule):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ITERATIONS = HwParam(15)

    def _declr(self):
        addClkRstn(self)

        self.cntrl = HwIORdVldSync()

        self.COUNTER_WIDTH = log2ceil(self.ITERATIONS)
        self.index = HwIOVectSignal(self.COUNTER_WIDTH)._m()
        self.body = HwIORdVldSync()._m()
        self.bodyBreak = HwIOSignal()

    def _impl(self):
        ITERATIONS = int(self.ITERATIONS)
        """
        Iterates from ITERATIONS -1 to 0 body is enabled by bodyVld and if bodyRd
        then counter is decremented for next iteration
        break causes reset of counter
        """

        counter = self._reg("counter", HBits(self.COUNTER_WIDTH), ITERATIONS - 1)

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
    from hwt.synth import to_rtl_str
    
    m = StaticForLoopCntrl()
    print(to_rtl_str(m))
