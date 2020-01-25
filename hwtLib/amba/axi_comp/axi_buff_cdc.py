#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import isPow2
from hwt.interfaces.std import Clk, Rst_n
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_comp.axi_buff import AxiBuff
from hwtLib.amba.axis_comp.builder import AxiSBuilder


class AxiBuffCdc(AxiBuff):
    """
    Clock domain crossing with buffers for AXI3/4/Lite and others

    :note: for DEPTH = 1 CDC register is used, else AsyncFifo
    .. hwt-schematic:: _example_AxiBuffCdc
    """

    def _config(self):
        AxiBuff._config(self)
        self.ADDR_BUFF_DEPTH += 1
        self.DATA_BUFF_DEPTH += 1
        self.M_FREQ = Param(int(102e6))
        self.S_FREQ = Param(int(102e6))

    def _declr(self):
        super(AxiBuffCdc, self)._declr()
        self.clk.FREQ = self.M_FREQ
        self.rst_n._make_association(clk=self.clk)

        self.m._make_association(clk=self.clk, rst=self.rst_n)

        self.s_clk = Clk()
        self.s_clk.FREQ = self.S_FREQ

        self.s_rst_n = Rst_n()
        self.s_rst_n._make_association(clk=self.s_clk)

        self.s._make_association(clk=self.s_clk, rst=self.s_rst_n)
        assert self.ADDR_BUFF_DEPTH == 1 or isPow2(self.ADDR_BUFF_DEPTH - 1), (
            self.ADDR_BUFF_DEPTH, "size 2**n + 1 for output reg")
        assert self.DATA_BUFF_DEPTH == 1 or isPow2(self.DATA_BUFF_DEPTH - 1), (
            self.DATA_BUFF_DEPTH, "size 2**n + 1 for output reg")

    def _impl(self):
        ADDR_DEPTH = self.ADDR_BUFF_DEPTH
        DATA_DEPTH = self.DATA_BUFF_DEPTH
        for name, m, s, depth in [("ar", self.m.ar, self.s.ar, ADDR_DEPTH),
                                  ("aw", self.m.aw, self.s.aw, ADDR_DEPTH),
                                  ("w", self.m.w, self.s.w, DATA_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff_cdc(
                items=depth,
                clk=self.s_clk,
                rst=self.s_rst_n,
            ).end
            s(i)

        for name, m, s, depth in [("r", self.s.r, self.m.r, DATA_DEPTH),
                                  ("b", self.s.b, self.m.b, ADDR_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff_cdc(
                items=depth,
                clk=self.clk,
                rst=self.rst_n,
            ).end
            s(i)


def _example_AxiBuffCdc():
    from hwtLib.amba.axi4 import Axi4
    u = AxiBuffCdc(Axi4)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiBuffCdc()
    print(toRtl(u))
