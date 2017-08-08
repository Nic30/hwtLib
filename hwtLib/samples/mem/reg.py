#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.types.defs import BIT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRst, propagateClkRst
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.code import If, Concat
from hwt.hdlObjects.typeShortcuts import vecT

"""
:note: everything in hwtLib.samples is just example
    and it is usually more elegant way to do this
"""


class DReg(Unit):
    """
    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype
    """
    def _declr(self):
        addClkRst(self)

        self.din = Signal(dtype=BIT)
        self.dout = Signal(dtype=BIT)

    def _impl(self):
        internReg = self._reg("internReg", BIT, defVal=False)

        internReg ** self.din
        self.dout ** internReg


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

        self.reg0.din ** self.din
        self.reg1.din ** self.reg0.dout
        self.dout ** self.reg1.dout


class AsyncResetReg(DReg):
    def _impl(self):
        internReg = self._sig("internReg", BIT, defVal=False)

        If(self.rst._isOn(),
           internReg ** 0,
        ).Elif(self.clk._onRisingEdge(),
           internReg ** self.din,
        )
        self.dout ** internReg


class DDR_Reg(Unit):
    def _declr(self):
        addClkRst(self)

        self.din = Signal(dtype=BIT)
        self.dout = Signal(dtype=vecT(2))

    def _impl(self):
        din = self.din

        internReg = [self._sig("internReg", BIT, defVal=False) for _ in range(2)]

        If(self.clk._onRisingEdge(),
           internReg[0] ** din,
        )
        If(self.clk._onFallingEdge(),
           internReg[1] ** din,
        )
        self.dout ** Concat(*internReg)


class OptimizedOutReg(DReg):
    def _impl(self):
        DReg._impl(self)
        self._reg("unconnected")

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = DDR_Reg()
    print(toRtl(u))
