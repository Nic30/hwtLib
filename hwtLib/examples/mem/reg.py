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
from hwt.pyUtils.typingFuture import override


class DReg(HwModule):
    """
    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRst(self)

        self.din = HwIOSignal()
        self.dout = HwIOSignal()._m()

    @override
    def hwImpl(self):
        internReg = self._reg("internReg", BIT, def_val=False)

        internReg(self.din)
        self.dout(internReg)


class DoubleDReg(HwModule):
    """
    :attention: using DReg unit instance is pointless because it can be instantiated
        by _reg in this unit

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        DReg.hwDeclr(self)

        self.reg0 = DReg()
        self.reg1 = DReg()

    @override
    def hwImpl(self):
        propagateClkRst(self)

        self.reg0.din(self.din)
        self.reg1.din(self.reg0.dout)
        self.dout(self.reg1.dout)


class AsyncResetReg(DReg):
    """
    .. hwt-autodoc::
    """
    @override
    def hwImpl(self):
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
    @override
    def hwDeclr(self):
        addClkRst(self)

        self.din = HwIOSignal(dtype=BIT)
        self.dout = HwIOVectSignal(2)._m()

    @override
    def hwImpl(self):
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
    @override
    def hwImpl(self):
        # add and conect register as it is in DReg
        DReg.hwImpl(self)
        # add an extra unconnected register which will be automatically removed
        self._reg("unconnected")


class RegWhereNextIsOnlyOutput(DReg):
    """
    (This is an error example)
    """
    @override
    def hwImpl(self):
        r = self._reg("r")
        # if clk._risingEdge():
        #    r = r._rtlNextSig
        # r._rtlNextSig = r
        self.dout(r._rtlNextSig)


class LatchReg(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.din = HwIOSignal()
        self.dout = HwIOSignal()._m()
        self.en = HwIOSignal()

    @override
    def hwImpl(self):
        # dout is latched because write into it is conditional
        # and it is not sychronized by any clock
        If(self.en,
           self.dout(self.din)
        )


class DReg_asyncRst(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        DReg.hwDeclr(self)

    @override
    def hwImpl(self):
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
