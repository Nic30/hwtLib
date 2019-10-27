#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit


class SelfRefCntr(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        self.dt = Bits(8, signed=False)

        addClkRstn(self)

        self.dout = Signal(dtype=self.dt)._m()

    def _impl(self):
        cntr = self._reg("cntr", self.dt, def_val=0)

        If(cntr._eq(4),
           cntr(0)
        ).Else(
           cntr(cntr + 1)
        )

        self.dout(cntr)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(SelfRefCntr()))
