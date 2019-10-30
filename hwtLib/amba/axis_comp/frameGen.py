#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, connect, log2ceil
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axis import AxiStream
from pyMathBitPrecise.bit_utils import mask


class AxisFrameGen(Unit):
    """
    Generator of axi stream frames for testing purposes

    .. hwt-schematic::
    """
    def _config(self):
        self.MAX_LEN = Param(511)
        self.CNTRL_ADDR_WIDTH = Param(4)
        self.CNTRL_DATA_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.axis_out = AxiStream()._m()

        with self._paramsShared(prefix="CNTRL_"):
            self.cntrl = Axi4Lite()

            reg_t = Bits(self.CNTRL_DATA_WIDTH)
            self.conv = AxiLiteEndpoint(
                            HStruct((reg_t, "enable"),
                                    (reg_t, "len")
                                    )
                            )

    def _impl(self):
        propagateClkRstn(self)
        cntr = self._reg("wordCntr", Bits(log2ceil(self.MAX_LEN)), def_val=0)
        en = self._reg("enable", def_val=0)
        _len = self._reg("wordCntr", Bits(log2ceil(self.MAX_LEN)), def_val=0)

        self.conv.bus(self.cntrl)
        cEn = self.conv.decoded.enable
        If(cEn.dout.vld,
           connect(cEn.dout.data, en, fit=True)
        )
        connect(en, cEn.din, fit=True)

        cLen = self.conv.decoded.len
        If(cLen.dout.vld,
           connect(cLen.dout.data, _len, fit=True)
        )
        connect(_len, cLen.din, fit=True)

        out = self.axis_out
        connect(cntr, out.data, fit=True)
        if self.USE_STRB:
            out.strb(mask(self.axis_out.strb._dtype.bit_length()))
        out.last(cntr._eq(0))
        out.valid(en)

        If(cLen.dout.vld,
           connect(cLen.dout.data, cntr, fit=True)
        ).Else(
            If(out.ready & en,
               If(cntr._eq(0),
                  cntr(_len)
               ).Else(
                  cntr(cntr - 1)
               )
            )
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxisFrameGen()
    print(toRtl(u))

    # import os
    # hwt.serializer.ip_packager import IpPackager
    # p = IpPackager(u)
    # p.createPackage(os.path.expanduser("~/Documents/test_ip_repo/"))
