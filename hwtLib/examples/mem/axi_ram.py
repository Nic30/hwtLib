#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axi_comp.builder import AxiBuilder
from hwtLib.mem.ram import RamSingleClock


class Axi4BRam(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self) -> None:
        Axi4._config(self)
        self.DATA_WIDTH = 512
        self.ADDR_WIDTH = 10

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = Axi4()
            self.ram = RamSingleClock()
            self.ram.ADDR_WIDTH = self.ADDR_WIDTH - log2ceil(self.DATA_WIDTH // 8 - 1)

    def _impl(self) -> None:
        ram = self.ram
        al = AxiBuilder(self, self.s).to_axi(Axi4Lite).end
        with self._paramsShared():
            dec = self.decoder = AxiLiteEndpoint(HStruct(
                    (ram.port[0].dout._dtype[2 ** ram.ADDR_WIDTH], "ram")
                ))

        dec.bus(al)
        ram.port[0](dec.decoded.ram)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Axi4BRam()
    print(to_rtl_str(u))
