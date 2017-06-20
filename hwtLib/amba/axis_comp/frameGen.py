from hwt.bitmask import mask
from hwt.code import If, connect, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axis import AxiStream


class AxisFrameGen(Unit):
    """
    Generator of axi stream frames for testing purposes
    """
    def _config(self):
        self.MAX_LEN = Param(511)
        self.CNTRL_AW = Param(4)
        self.CNTRL_DW = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.axis_out = AxiStream()

        self.cntrl = AxiLite()
        self.cntrl._replaceParam("ADDR_WIDTH", self.CNTRL_AW)
        self.cntrl._replaceParam("DATA_WIDTH", self.CNTRL_DW)

        self.conv = AxiLiteEndpoint(
                        HStruct((vecT(self.CNTRL_DW), "enable"),
                                (vecT(self.CNTRL_DW), "len")
                                )
                        )
        self.conv.ADDR_WIDTH.set(self.CNTRL_AW)
        self.conv.DATA_WIDTH.set(self.CNTRL_DW)

    def _impl(self):
        propagateClkRstn(self)
        cntr = self._reg("wordCntr", vecT(log2ceil(self.MAX_LEN)), defVal=0)
        en = self._reg("enable", defVal=0)
        _len = self._reg("wordCntr", vecT(log2ceil(self.MAX_LEN)), defVal=0)

        self.conv.bus ** self.cntrl
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
        out.strb ** mask(self.axis_out.strb._dtype.bit_length())
        out.last ** cntr._eq(0)
        out.valid ** en

        If(cLen.dout.vld,
           connect(cLen.dout.data, cntr, fit=True)
        ).Else(
            If(out.ready & en,
               If(cntr._eq(0),
                  cntr ** _len
               ).Else(
                  cntr ** (cntr - 1) 
               )
            )
        )


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxisFrameGen()
    print(toRtl(u))

    # import os
    # hwt.serializer.packager import Packager
    # p = Packager(u)
    # p.createPackage(os.path.expanduser("~/Documents/test_ip_repo/")) 
