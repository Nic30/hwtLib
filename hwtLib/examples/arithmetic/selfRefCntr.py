#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class SelfRefCntr(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.dt = HBits(8, signed=False)

        addClkRstn(self)

        self.dout = HwIOSignal(dtype=self.dt)._m()

    @override
    def hwImpl(self):
        cntr = self._reg("cntr", self.dt, def_val=0)

        If(cntr._eq(4),
           cntr(0)
        ).Else(
           cntr(cntr + 1)
        )

        self.dout(cntr)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    print(to_rtl_str(SelfRefCntr()))
