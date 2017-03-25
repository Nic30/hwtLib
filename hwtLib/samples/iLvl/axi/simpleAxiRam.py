#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.axiLite_comp.structEndpoint import AxiLiteStructEndpoint
from hwtLib.mem.ram import RamSingleClock


class SimpleAxiRam(Unit):
    """
    Example of axi lite mapped register and ram
    0x0 - reg0
    0x4 - ram0, size: 1024 words
    """
    def _config(self):
        self.ADDR_WIDTH = Param(16)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.axi = AxiLite()

        with self._paramsShared():
            t = vecT(self.DATA_WIDTH)
            self.conv = AxiLiteStructEndpoint(
                            HStruct((t, "reg0"),
                                    (Array(t, 512), "ram0")
                                    )
                            )

        self.ram = RamSingleClock()
        self.ram.ADDR_WIDTH.set(9)
        self.ram.DATA_WIDTH.set(self.DATA_WIDTH)

    def _impl(self):
        propagateClkRstn(self)
        self.conv.bus ** self.axi

        reg0 = self._reg("reg0", vecT(32), defVal=0)

        conv = self.conv
        If(conv.reg0.dout.vld,
            reg0 ** conv.reg0.dout.data
        )
        conv.reg0.din ** reg0

        self.ram.a ** conv.ram0

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = SimpleAxiRam()
    print(toRtl(u))
