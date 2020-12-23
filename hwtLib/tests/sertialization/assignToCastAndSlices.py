#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Problem list:

* next of the register should be driven from
* all assignments to a register has to be in stame process.
* The nop assignment should assign only a reange which corresponds to a current range assigned by statement.

"""

from hwt.code import If
from hwt.interfaces.std import VectSignal, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs, \
    AddrDataBitMaskHs
from pyMathBitPrecise.bit_utils import mask


class AssignToASlice0(Unit):
    """
    Conversion between vector and bit
    """

    def _declr(self):
        addClkRstn(self)
        self.data_in = Signal()
        self.data_out = VectSignal(1)._m()

    def _impl(self):
        self.data_out[0](self.data_in)


class AssignToASlice1(Unit):
    """
    Vector parts driven by expr
    """

    def _declr(self):
        addClkRstn(self)
        self.data_in = VectSignal(3)
        self.data_out = VectSignal(3)._m()

    def _impl(self):
        for i in range(3):
            self.data_out[i](self.data_in[i])


class AssignToASlice2(Unit):
    """
    Vector parts driven from multi branch statement
    """

    def _declr(self):
        addClkRstn(self)
        self.swap = Signal()
        self.data_in = VectSignal(2)
        self.data_out = VectSignal(3)._m()

    def _impl(self):
        i, o = self.data_in, self.data_out
        If(self.swap,
           o[0](i[1]),
           o[1](i[0]),
           o[2](i[0]),
        ).Else(
           o[0](i[0]),
           o[1](i[1]),
           o[2](i[1]),
        )


class AssignToASliceOfReg0(Unit):
    """
    Register where slices of next signal are set conditionally
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = AddrDataHs()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 8
        self.data_out = VectSignal(2 * 8)._m()

    def _impl(self):
        i, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        i.rd(1)
        for _i in range(2):
            start = 8 * _i
            If(i.vld & i.addr._eq(_i),
               r[start + 8:start](i.data)
            )
        o(r)


class AssignToASliceOfReg1a(Unit):
    """
    Register where slices of next signal are set conditionally in multiple branches
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = AddrDataHs()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 16
        self.data_out = VectSignal(2 * 8)._m()

    def _impl(self):
        i, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        i.rd(1)
        If(i.vld & i.addr._eq(0),
           r[8:](i.data[8:]),
           r[:8](i.data[:8]),
        ).Elif(i.vld & i.addr._eq(1),
           r[8:](i.data[:8]),
           r[:8](i.data[8:]),
        )
        o(r)


class AssignToASliceOfReg1b(Unit):
    """
    Register where slices of next signal are set conditionally in multiple branches, nested
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = AddrDataHs()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 16
        self.data_out = VectSignal(2 * 8)._m()

    def _impl(self):
        i, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        i.rd(1)
        If(i.vld,
            If(i.addr._eq(0),
               r[8:](i.data[8:]),
               r[:8](i.data[:8]),
            ).Elif(i.addr._eq(1),
               r[8:](i.data[:8]),
               r[:8](i.data[8:]),
            )
        )
        o(r)


class AssignToASliceOfReg2a(Unit):
    """
    Register where an overlapping slices of next signal are set conditionally
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = AddrDataBitMaskHs()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 8
        self.data_out = VectSignal(2 * 8)._m()

    def _impl(self):
        i, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        i.rd(1)
        for _i in range(2):
            start = 8 * _i
            If(i.vld & i.addr._eq(_i),
               If(i.mask._eq(mask(8)),
                  r[start + 8:start](i.data)
               ).Elif(i.mask._eq(mask(4)),
                  r[start + 4:start](i.data[4:])
               )
            )
        o(r)


class AssignToASliceOfReg2b(Unit):
    """
    Register where an overlapping slices of next signal are set conditionally
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = AddrDataBitMaskHs()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 8
        self.data_out = VectSignal(2 * 8)._m()

    def _impl(self):
        i, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        i.rd(1)
        for _i in range(2):
            start = 8 * _i
            If(i.vld & i.addr._eq(_i),
               If(i.mask._eq(mask(8)),
                  r[start + 8:start](i.data)
               ).Elif(i.mask._eq(mask(4)),
                  r[start + 8:start + 4](i.data[4:])
               )
            )
        o(r)


if __name__ == '__main__':
    from hwt.synthesizer.utils import to_rtl_str

    print(to_rtl_str(AssignToASliceOfReg2a()))

