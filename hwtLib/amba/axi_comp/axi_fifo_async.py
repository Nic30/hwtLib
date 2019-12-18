#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Clk, Rst_n
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axi_comp.axi_buff import AxiBuff
from hwt.code import isPow2


class AxiClockDomainCrossing(AxiBuff):
    """
    Clock domain crossing with buffers for AXI3/4/Lite and others
    """

    def _config(self):
        AxiBuff._config(self)
        self.ADDR_BUFF_DEPTH += 1
        self.DATA_BUFF_DEPTH += 1

    def _declr(self):
        super(AxiClockDomainCrossing, self)._declr()
        self.s_clk = Clk()
        self.s._make_association(clk=self.s_clk)
        assert isPow2(self.ADDR_BUFF_DEPTH - 1), self.ADDR_BUFF_DEPTH
        assert isPow2(self.DATA_BUFF_DEPTH - 1), self.DATA_BUFF_DEPTH

    def _impl(self)->None:
        ADDR_DEPTH = self.ADDR_BUFF_DEPTH
        DATA_DEPTH = self.DATA_BUFF_DEPTH
        for name, m, s, depth in [("ar", self.m.ar, self.s.ar, ADDR_DEPTH),
                                  ("aw", self.m.aw, self.s.aw, ADDR_DEPTH),
                                  ("w", self.m.w, self.s.w, DATA_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff_cdc(
                items=depth,
                clk=self.s_clk,
            ).end
            s(i)

        for name, m, s, depth in [("r", self.s.r, self.m.r, DATA_DEPTH),
                                  ("b", self.s.b, self.m.b, ADDR_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff_cdc(
                items=depth,
                clk=self.clk,
            ).end
            s(i)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    from hwtLib.amba.axi4 import Axi4
    u = AxiClockDomainCrossing(Axi4)
    print(toRtl(u))
