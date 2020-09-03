#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, log2ceil
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataVldHs, AddrDataHs


@serializeParamsUniq
class Cam(Unit):
    """
    Content addressable memory.
    MATCH_LATENCY = 1

    :note: Simple combinational version

    .. hwt-schematic::
    """

    def _config(self):
        self.KEY_WIDTH = Param(15)
        self.ITEMS = Param(32)
        self.USE_VLD_BIT = Param(True)

    def _declr(self):
        addClkRstn(self)
        self.match = m = Handshaked()
        m.DATA_WIDTH = self.KEY_WIDTH

        # address is index of CAM cell, data is key to store
        if self.USE_VLD_BIT:
            w = AddrDataVldHs()
        else:
            w = AddrDataHs()
        self.write = w
        w.DATA_WIDTH = self.KEY_WIDTH
        w.ADDR_WIDTH = log2ceil(self.ITEMS - 1)

        # one hot encoded
        self.out = o = Handshaked()._m()
        o.DATA_WIDTH = self.ITEMS

    def writeHandler(self, mem):
        w = self.write
        w.rd(1)

        key_data = w.data
        if self.USE_VLD_BIT:
            key_data = Concat(w.data, w.vld_flag)

        If(self.clk._onRisingEdge() & w.vld,
           mem[w.addr](key_data)
        )

    def matchHandler(self, mem):
        key = self.match

        key.rd(self.out.rd)

        key_data = key.data
        if self.USE_VLD_BIT:
            key_data = Concat(key.data, hBit(1))

        out_one_hot = []
        for i in range(self.ITEMS):
            b = mem[i]._eq(key_data)
            out_one_hot.append(b)

        self.out.data(Concat(*reversed(out_one_hot)))
        self.out.vld(key.vld)

    def _impl(self):
        KEY_WIDTH = self.KEY_WIDTH
        if self.USE_VLD_BIT:
            # +1 bit to validity check
            KEY_WIDTH += 1

        self._mem = self._sig("cam_mem",
                              Bits(KEY_WIDTH)[self.ITEMS],
                              [0 for _ in range(self.ITEMS)]
                              )
        self.writeHandler(self._mem)
        self.matchHandler(self._mem)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Cam()
    print(to_rtl_str(u))
