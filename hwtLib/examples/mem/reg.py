#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
:note: everything in hwtLib.examples is just example
    and it is usually more elegant way to do this
"""

from hwt.code import If, Concat
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRst, propagateClkRst
from hwt.hwModule import HwModule


class DReg(HwModule):
    """
    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype

    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRst(self)

        self.din = HwIOSignal()
        self.dout = HwIOSignal()._m()

    def _impl(self):
        internReg = self._reg("internReg", BIT, def_val=False)

        internReg(self.din)
        self.dout(internReg)


class DoubleDReg(HwModule):
    """
    :attention: using DReg unit instance is pointless because it can be instantiated
        by _reg in this unit

    .. hwt-autodoc::
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
    """
    .. hwt-autodoc::
    """
    def _impl(self):
        internReg = self._sig("internReg", BIT, def_val=False)

        If(self.rst._isOn(),
           internReg(0),
        ).Elif(self.clk._onRisingEdge(),
           internReg(self.din),
        )
        self.dout(internReg)


class DDR_Reg(HwModule):
    """
    Double Data Rate register

    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRst(self)

        self.din = HwIOSignal(dtype=BIT)
        self.dout = HwIOVectSignal(2)._m()

    def _impl(self):
        din = self.din

        internReg = [self._sig("internReg", BIT, def_val=False) for _ in range(2)]

        If(self.clk._onRisingEdge(),
           internReg[0](din),
        )
        If(self.clk._onFallingEdge(),
           internReg[1](din),
        )
        self.dout(Concat(*internReg))


class OptimizedOutReg(DReg):
    """
    .. hwt-autodoc::
    """
    def _impl(self):
        # add and conect register as it is in DReg
        DReg._impl(self)
        # add an extra unconnected register which will be automatically removed
        self._reg("unconnected")


class RegWhereNextIsOnlyOutput(DReg):
    """
    (This is an error example)
    """
    def _impl(self):
        r = self._reg("r")
        # if clk._risingEdge():
        #    r = r.next
        # r.next = r
        self.dout(r.next)


class LatchReg(HwModule):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.din = HwIOSignal()
        self.dout = HwIOSignal()._m()
        self.en = HwIOSignal()

    def _impl(self):
        # dout is latched because write into it is conditional
        # and it is not sychronized by any clock
        If(self.en,
           self.dout(self.din)
        )


class DReg_asyncRst(HwModule):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        DReg._declr(self)

    def _impl(self):
        r = self._sig("r")

        # "r" has reset which is not dependent on on "clk"
        If(self.rst._isOn(),
           r(0)
        ).Elif(self.clk._onRisingEdge(),
           r(self.din)
        )

        self.dout(r)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = OptimizedOutReg()
    print(to_rtl_str(m))
