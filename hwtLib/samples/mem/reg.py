#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
:note: everything in hwtLib.samples is just example
    and it is usually more elegant way to do this
"""

from hwt.code import If, Concat
from hwt.hdl.types.defs import BIT
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRst, propagateClkRst
from hwt.synthesizer.unit import Unit


class DReg(Unit):
    """
    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype
    """
    def _declr(self):
        addClkRst(self)

        self.din = Signal()
        self.dout = Signal()._m()

    def _impl(self):
        internReg = self._reg("internReg", BIT, defVal=False)

        internReg(self.din)
        self.dout(internReg)


class DoubleDReg(Unit):
    """
    :attention: using DReg unit instance is pointless because it can be instantiated
        by _reg in this unit
    """
    def _declr(self):
        DReg._declr(self)

        self.reg0 = DReg()
        self.reg1 = DReg()

    def _impl(self):
        propagateClkRst(self)

        self.reg0.din(self.din)
        self.reg1.din(self.reg0.dout)
        self.dout(self.reg1.dout)


class AsyncResetReg(DReg):
    def _impl(self):
        internReg = self._sig("internReg", BIT, defVal=False)

        If(self.rst._isOn(),
           internReg(0),
        ).Elif(self.clk._onRisingEdge(),
           internReg(self.din),
        )
        self.dout(internReg)


class DDR_Reg(Unit):
    def _declr(self):
        addClkRst(self)

        self.din = Signal(dtype=BIT)
        self.dout = VectSignal(2)._m()

    def _impl(self):
        din = self.din

        internReg = [self._sig("internReg", BIT, defVal=False) for _ in range(2)]

        If(self.clk._onRisingEdge(),
           internReg[0](din),
        )
        If(self.clk._onFallingEdge(),
           internReg[1](din),
        )
        self.dout(Concat(*internReg))


class OptimizedOutReg(DReg):
    def _impl(self):
        DReg._impl(self)
        self._reg("unconnected")


class Latch(Unit):
    """
    Example showing how to implement latch in hwt
    """
    def _declr(self):
        self.din = Signal()
        self.dout = Signal()._m()
        self.en = Signal()

    def _impl(self):
        If(self.en,
           self.dout(self.din)
        )


class DReg_asyncRst(Unit):
    def _declr(self):
        DReg._declr(self)

    def _impl(self):
        r = self._sig("r")
        If(self.rst._isOn(),
           r(0)
        ).Elif(self.clk._onRisingEdge(),
           r(self.din)
        )

        self.dout(r)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = DDR_Reg()
    print(toRtl(u))
