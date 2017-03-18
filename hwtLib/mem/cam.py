#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT, hBit
from hwt.hdlObjects.types.array import Array
from hwt.interfaces.std import Handshaked, VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.interfaces.addrDataHs import AddrDataBitMaskHs


class Cam(Unit):
    """
    Content addressable memory

    Simple combinational version

    MATCH_LATENCY = 1
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ

    def _config(self):
        self.DATA_WIDTH = Param(36)
        self.ITEMS = Param(16)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.match = Handshaked()
            self.write = AddrDataBitMaskHs()
            self.write.ADDR_WIDTH.set(log2ceil(self.ITEMS - 1))
        self.out = VldSynced()
        self.out._replaceParam("DATA_WIDTH", self.ITEMS)

    def writeHandler(self, mem):
        w = self.write
        w.rd ** 1

        If(self.clk._onRisingEdge() & w.vld,
           mem[w.addr] ** Concat(w.data, w.mask[0])
        )

    def matchHandler(self, mem):
        key = self.match

        out = self._reg("out_reg", self.out.data._dtype, defVal=0)
        outNext = out.next
        outVld = self._reg("out_vld_reg", defVal=0)

        key.rd ** 1
        outVld ** key.vld

        for i in range(evalParam(self.ITEMS).val):
            outNext[i] ** mem[i]._eq(Concat(key.data, hBit(1)))

        self.out.data ** out
        self.out.vld ** outVld 

    def _impl(self):
        # +1 bit to validity check
        self._mem = self._sig("cam_mem", Array(vecT(self.DATA_WIDTH + 1), 
                                               self.ITEMS),
                                               [0 for _ in range(evalParam(self.ITEMS).val)])
        self.writeHandler(self._mem)
        self.matchHandler(self._mem)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = Cam()
    print(toRtl(u))
