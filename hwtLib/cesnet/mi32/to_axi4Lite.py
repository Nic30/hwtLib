#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.constants import PROT_DEFAULT
from hwtLib.cesnet.mi32.intf import Mi32
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.defs import BIT
from hwt.code import If


class Mi32_to_Axi4Lite(BusBridge):
    """
    Bridge from MI32 interface to AxiLite interface

    :attention: requires ar.valid & aw.valid & w.ready to be 1 in order to perform a transation
        (This may require an extra AXI4Lite register to avoid deadlock for components which are waiting
        for end of transaction on other channel r/w)

    .. hwt-autodoc::
    """

    def _config(self):
        Axi4Lite._config(self)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.m = Axi4Lite()._m()
            self.s = Mi32()

    def _impl(self):
        mi32 = self.s
        axi = self.m
        w_data = self._reg("w_data", HStruct(
            (axi.w.data._dtype, "data"),
            (axi.w.strb._dtype, "strb"),
            (BIT, "pending"),
        ), def_val={"pending": 0})
        w_data_clean = (~w_data.pending | axi.w.ready)
        mi32.ardy(axi.ar.ready & axi.aw.ready & w_data_clean)
        axi.ar.addr(mi32.addr)
        axi.ar.valid(mi32.rd & axi.aw.ready)
        axi.ar.prot(PROT_DEFAULT)
        axi.aw.addr(mi32.addr)
        w_en = mi32.wr & axi.ar.ready
        axi.aw.valid(w_en & w_data_clean)
        axi.aw.prot(PROT_DEFAULT)

        If(w_data.pending,
            If(axi.w.ready,
                If(w_en & axi.aw.ready,
                    w_data.data(mi32.dwr),
                    w_data.strb(mi32.be),
                ).Else(
                    w_data.data(None),
                    w_data.strb(None),
                    w_data.pending(0),
                )
            )
        ).Else(
            w_data.pending(w_en & axi.aw.ready),
            w_data.data(mi32.dwr),
            w_data.strb(mi32.be),
        )
        axi.w.data(w_data.data)
        axi.w.strb(w_data.strb)
        axi.w.valid(w_data.pending)
        axi.b.ready(1)

        mi32.drdy(axi.r.valid)
        mi32.drd(axi.r.data)
        axi.r.ready(1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Mi32_to_Axi4Lite()
    print(to_rtl_str(u))
