#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.types.ctypes import uint32_t


class SimpleAxiRegs(HwModule):
    """
    Axi litle mapped registers example,
    0x0 - reg0
    0x4 - reg1

    .. hwt-autodoc::
    """
    def _config(self):
        self.ADDR_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(32)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.axi = Axi4Lite()

        with self._hwParamsShared():
            # this structure is configuration of interfaces
            # fields can also be arrays and metaclass can be used
            # to specify field interface and R/W access to field
            self.conv = AxiLiteEndpoint(
                            HStruct((uint32_t, "reg0"),
                                    (uint32_t, "reg1")
                                    ))

    def _impl(self):
        propagateClkRstn(self)
        self.conv.bus(self.axi, fit=True)

        reg0 = self._reg("reg0", HBits(32), def_val=0)
        reg1 = self._reg("reg1", HBits(32), def_val=1)

        conv = self.conv

        def connectRegToConveror(convPort, reg):
            If(convPort.dout.vld,
                reg(convPort.dout.data)
            )
            convPort.din(reg)

        connectRegToConveror(conv.decoded.reg0, reg0)
        connectRegToConveror(conv.decoded.reg1, reg1)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = SimpleAxiRegs()
    print(to_rtl_str(m))
