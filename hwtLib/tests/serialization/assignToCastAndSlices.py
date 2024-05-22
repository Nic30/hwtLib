#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Problem list:

* next signal of the register should be driven from assignment source
* all assignments to a register has to be in the same process.
* The nop assignment should assign only a range which corresponds to a current range assigned by statement.

"""

from hwt.code import If, Switch
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwtLib.commonHwIO.addr_data import HwIOAddrDataRdVld, \
    HwIOAddrDataBitMaskRdVld
from pyMathBitPrecise.bit_utils import mask


class AssignToASlice0(HwModule):
    """
    Conversion between vector and bit
    """

    def _declr(self):
        addClkRstn(self)
        self.data_in = HwIOSignal()
        self.data_out = HwIOVectSignal(1)._m()

    def _impl(self):
        self.data_out[0](self.data_in)


class AssignToASlice1(HwModule):
    """
    Vector parts driven by expr
    """

    def _declr(self):
        addClkRstn(self)
        self.data_in = HwIOVectSignal(3)
        self.data_out = HwIOVectSignal(3)._m()

    def _impl(self):
        for i in range(3):
            self.data_out[i](self.data_in[i])


class AssignToASlice2(HwModule):
    """
    Vector parts driven from multi branch statement
    """

    def _declr(self):
        addClkRstn(self)
        self.swap = HwIOSignal()
        self.data_in = HwIOVectSignal(2)
        self.data_out = HwIOVectSignal(3)._m()

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


class AssignToASliceOfReg0(HwModule):
    """
    Register where slices of next signal are set conditionally
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = HwIOAddrDataRdVld()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 8
        self.data_out = HwIOVectSignal(2 * 8)._m()

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


class AssignToASliceOfReg1a(HwModule):
    """
    Register where slices of next signal are set conditionally in multiple branches
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = HwIOAddrDataRdVld()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 16
        self.data_out = HwIOVectSignal(2 * 8)._m()

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


class AssignToASliceOfReg1b(HwModule):
    """
    Register where slices of next signal are set conditionally in multiple branches, nested
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = HwIOAddrDataRdVld()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 16
        self.data_out = HwIOVectSignal(2 * 8)._m()

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


class AssignToASliceOfReg2a(HwModule):
    """
    Register where an overlapping slices of next signal are set conditionally
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = HwIOAddrDataBitMaskRdVld()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 8
        self.data_out = HwIOVectSignal(2 * 8)._m()

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


class AssignToASliceOfReg2b(HwModule):
    """
    Register where an overlapping slices of next signal are set conditionally
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = HwIOAddrDataBitMaskRdVld()
        i.ADDR_WIDTH = 1
        i.DATA_WIDTH = 8
        self.data_out = HwIOVectSignal(2 * 8)._m()

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


class AssignToASliceOfReg3a(HwModule):
    """
    Something not assigned by index at the end and then whole signal assigned.
    """

    def _declr(self):
        addClkRstn(self)
        i = self.data_in = HwIOAddrDataBitMaskRdVld()
        i.ADDR_WIDTH = 2
        i.DATA_WIDTH = 8
        self.data_out = HwIOVectSignal(4 * 8)._m()

    def _impl(self):
        din, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        Switch(din.addr).add_cases(
            ((i, r[(i + 1) * 8:i * 8](din.data))
             for i in range(3))
        ).Default(
            r(123)
        )
        din.rd(1)
        o(r)


class AssignToASliceOfReg3b(AssignToASliceOfReg3a):
    """
    Something not assigned by index in the middle and then whole signal assigned.
    """

    def _impl(self):
        din, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        Switch(din.addr)\
        .Case(0,
              r[8:0](din.data)
        ).Case(2,
              r[24:16](din.data)
        ).Case(3,
              r[32:24](din.data)
        ).Default(
            r(123)
        )
        din.rd(1)
        o(r)


class AssignToASliceOfReg3c(AssignToASliceOfReg3a):
    """
    Something not assigned by index at the beggining and then whole signal assigned.
    """

    def _impl(self):
        din, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        Switch(din.addr).add_cases(
            ((i, r[(i + 1) * 8:i * 8](din.data))
             for i in range(1, 4))
        ).Default(
            r(123)
        )
        din.rd(1)
        o(r)

class AssignToASliceOfReg3d(AssignToASliceOfReg3a):
    """
    Only a small fragment assigned and then whole signal assigned.
    """

    def _impl(self):
        din, o = self.data_in, self.data_out
        r = self._reg("r", self.data_out._dtype, def_val=0)
        Switch(din.addr)\
        .Case(1,
              r[16:8](din.data)
        ).Default(
            r(123)
        )
        din.rd(1)
        o(r)

if __name__ == '__main__':
    from hwt.synth import to_rtl_str

    print(to_rtl_str(AssignToASliceOfReg3d()))

