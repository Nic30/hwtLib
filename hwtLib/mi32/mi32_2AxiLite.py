#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.constants import PROT_DEFAULT
from hwtLib.mi32.intf import Mi32


class Mi32_2AxiLite(BusBridge):
    """
    Bridge from MI32 interface to AxiLite interface
    
    :attention: requires ar.valid & aw.valid & w.ready to be 1 in order to perform a transation
        (This may require an extra AXI4Lite register to avoid deadlock for components which are waiting
        for end of transaction on oter channel r/w)

    .. hwt-schematic::
    """

    def _config(self) -> None:
        Axi4Lite._config(self)

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = Axi4Lite()._m()
            self.m = Mi32()

    def _impl(self) -> None:
        mi32 = self.m
        axi = self.s

        mi32.ardy(axi.ar.ready & axi.aw.ready & axi.w.ready)
        axi.ar.addr(mi32.addr)
        axi.ar.valid(mi32.rd & axi.aw.ready & axi.w.ready)
        axi.ar.prot(PROT_DEFAULT)
        axi.aw.addr(mi32.addr)
        axi.aw.valid(mi32.wr & axi.ar.ready & axi.w.ready)
        axi.aw.prot(PROT_DEFAULT)

        axi.w.data(mi32.dwr)
        axi.w.strb(mi32.be)
        axi.w.valid(mi32.wr & axi.ar.ready & axi.aw.ready)
        axi.b.ready(1)

        mi32.drdy(axi.r.valid)
        mi32.drd(axi.r.data)
        axi.r.ready(1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = Mi32_2AxiLite()
    print(toRtl(u))
