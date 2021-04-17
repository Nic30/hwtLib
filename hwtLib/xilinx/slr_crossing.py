#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.xilinx.primitive.lutAsShiftReg import LutAsShiftReg


class HsSlrCrossingIo(BusBridge):
    """
    An abstract class with a declaration of interfaces for handskaked SLR crosings
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = Handshaked()
            self.m = Handshaked()._m()


class SlrCrossingSrc(HsSlrCrossingIo):
    """
    A part of SLR crossing which should be placed in SLR of producer
    """

    def _impl(self):
        s, m = self.s, self.m
        reg = self._reg("reg", HStruct(
                (s.data._dtype, "data"),
                (BIT, "rd"),
                (BIT, "vld"),
            ),
            def_val={"vld": 0, "rd": 0}
        )

        reg.data(s.data)
        reg.vld(s.vld)
        s.rd(reg.rd)

        m.data(reg.data)
        m.vld(reg.vld)
        reg.rd(m.rd)


class SlrCrossingDst(HsSlrCrossingIo):
    """
    A part of SLR crossing which should be placed in SLR of consumer
    """

    def _declr(self):
        super(SlrCrossingDst, self)._declr()
        self.DEPTH = 4

        sh_d = LutAsShiftReg()
        sh_d.DATA_WIDTH = self.DATA_WIDTH
        sh_d.ITEMS = self.DEPTH
        self.shift_reg_data = sh_d

        sh_vld = LutAsShiftReg()
        sh_vld.DATA_WIDTH = 1
        sh_vld.ITEMS = self.DEPTH
        self.shift_reg_vld = sh_vld

    def _impl(self):
        DEPTH = self.DEPTH
        s, m = self.s, self.m

        out_valid = self._reg("out_valid", def_val=0)
        out_ce = rename_signal(self, m.rd | ~out_valid, "out_ce")
        in_ready = self._reg("in_ready", def_val=1)
        in_ready(out_ce)

        cross_ce_inreg = self._reg("cross_ce_inreg", def_val=1)
        cross_ce_inreg(in_ready)

        cross_ce = self._reg("cross_ce", def_val=1)
        cross_ce(cross_ce_inreg)

        sh_addr = self._reg("sh_push", Bits(log2ceil(DEPTH)), def_val=0)
        If(~out_ce & cross_ce,
           sh_addr(sh_addr + 1)
        ).Elif(out_ce & ~cross_ce,
           sh_addr(sh_addr - 1)
        )

        sh_vld = self.shift_reg_vld
        sh_data = self.shift_reg_data
        for sh in [sh_vld, sh_data]:
            sh.d_in.vld(cross_ce)
            sh.d_out_addr(sh_addr)

        sh_vld.d_in.data(s.vld)
        sh_data.d_in.data(s.data)
        s.rd(in_ready)

        data = self._reg("data", m.data._dtype)
        If(out_ce,
            data(sh_data.d_out),
            out_valid(sh_vld.d_out),
        )
        m.data(data)
        m.vld(out_valid)
        propagateClkRstn(self)


class HsSlrCrossing(HsSlrCrossingIo):
    """
    Super Logic Region (SLR) crossing for handshaked interfaces

    SLR represents one chiplet of FPGA which uses stacked silicon interconnect (SSI) or equivalent.
    The SLR corssing is required on SLR boundaries to met the timing.
    The crossing itself is just a pipeline of registers.
    """

    def _declr(self):
        HsSlrCrossingIo._declr(self)
        with self._paramsShared():
            self.src = SlrCrossingSrc()
            self.dst = SlrCrossingDst()

    def _impl(self):
        propagateClkRstn(self)
        src, dst = self.src, self.dst
        src.s(self.s)
        dst.s(src.m)
        self.m(dst.m)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = HsSlrCrossing()
    u.DATA_WIDTH = 4
    print(to_rtl_str(u))
