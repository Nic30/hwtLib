#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOClk, HwIORst_n
from hwt.hwParam import HwParam
from hwt.math import isPow2
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi_comp.buff import AxiBuff
from hwtLib.amba.axis_comp.builder import Axi4SBuilder


class AxiBuffCdc(AxiBuff):
    """
    Clock domain crossing with buffers for AXI3/4/Lite and others

    :note: for DEPTH = 1 CDC register is used, else AsyncFifo

    .. hwt-autodoc:: _example_AxiBuffCdc
    """

    @override
    def hwConfig(self):
        AxiBuff.hwConfig(self)
        self.ADDR_BUFF_DEPTH += 1
        self.DATA_BUFF_DEPTH += 1
        self.M_FREQ = HwParam(int(102e6))
        self.S_FREQ = HwParam(int(102e6))

    def _setup_clk_rst_n(self):
        self.clk.FREQ = self.M_FREQ
        self.rst_n._make_association(clk=self.clk)

        self.s._make_association(clk=self.clk, rst=self.rst_n)

        self.m_clk = HwIOClk()
        self.m_clk.FREQ = self.S_FREQ

        self.m_rst_n = HwIORst_n()
        self.m_rst_n._make_association(clk=self.m_clk)

        self.m._make_association(clk=self.m_clk, rst=self.m_rst_n)
        assert self.ADDR_BUFF_DEPTH == 1 or isPow2(self.ADDR_BUFF_DEPTH - 1), (
            self.ADDR_BUFF_DEPTH, "size 2**n + 1 for output reg")
        assert self.DATA_BUFF_DEPTH == 1 or isPow2(self.DATA_BUFF_DEPTH - 1), (
            self.DATA_BUFF_DEPTH, "size 2**n + 1 for output reg")

    @override
    def hwDeclr(self):
        super(AxiBuffCdc, self).hwDeclr()
        self._setup_clk_rst_n()

    @override
    def hwImpl(self):
        ADDR_DEPTH = self.ADDR_BUFF_DEPTH
        DATA_DEPTH = self.DATA_BUFF_DEPTH
        for name, m, s, depth in [("ar", self.s.ar, self.m.ar, ADDR_DEPTH),
                                  ("aw", self.s.aw, self.m.aw, ADDR_DEPTH),
                                  ("w",  self.s.w,  self.m.w, DATA_DEPTH)]:
            i = Axi4SBuilder(self, m, name).buff_cdc(
                items=depth,
                clk=self.m_clk,
                rst=self.m_rst_n,
            ).end
            s(i)

        for name, m, s, depth in [("r", self.m.r, self.s.r, DATA_DEPTH),
                                  ("b", self.m.b, self.s.b, ADDR_DEPTH)]:
            i = Axi4SBuilder(self, m, name).buff_cdc(
                items=depth,
                clk=self.clk,
                rst=self.rst_n,
            ).end
            s(i)


def _example_AxiBuffCdc():
    from hwtLib.amba.axi4 import Axi4
    m = AxiBuffCdc(Axi4)
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_AxiBuffCdc()
    print(to_rtl_str(m))
