#!/usr/bin/env python3
# -*- coding: utf-8 -

from hwt.code import log2ceil, connect, Concat, power
from hwt.interfaces.std import Handshaked, VectSignal
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.structManipulators.arrayItemGetter import ArrayItemGetter


class MMU_1pageLvl(Unit):
    """
    [TODO]
    """
    def _config(self):
        self.ID_WIDTH = Param(0)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

        self.VIRT_ADDR_WIDTH = Param(32)
        self.PAGE_SIZE = Param(int(2 ** 12))

        self.MAX_OVERLAP = Param(16)

    def _declr(self):
        addClkRstn(self)
        PAGE_OFFSET_BITS = log2ceil(self.PAGE_SIZE).val
        PAGE_TABLE_ITEMS = (power(2, self.ADDR_WIDTH)) // self.PAGE_SIZE

        with self._paramsShared():
            self.rDatapump = AxiRDatapumpIntf()
            self.rDatapump.MAX_LEN.set(1)
            self.itemGet = ArrayItemGetter()

        self.itemGet.ITEM_WIDTH.set(self.ADDR_WIDTH)
        self.itemGet.ITEMS.set(PAGE_TABLE_ITEMS)

        i = self.virtIn = Handshaked()
        i._replaceParam("DATA_WIDTH", self.VIRT_ADDR_WIDTH)

        i = self.physOut = Handshaked()
        i._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)

        self.pageOffsetFifo = HandshakedFifo(Handshaked)
        self.pageOffsetFifo.DEPTH.set(self.MAX_OVERLAP)
        self.pageOffsetFifo.DATA_WIDTH.set(PAGE_OFFSET_BITS)

        self.pageTableBase = VectSignal(self.ADDR_WIDTH)

    def _impl(self):
        propagateClkRstn(self)
        pageOffset = self.pageOffsetFifo
        PAGE_OFFSET_BITS = pageOffset.dataIn.data._dtype.bit_length()
        get = self.itemGet

        self.rDatapump ** get.rDatapump
        get.base ** self.pageTableBase

        # split page offset and send page index to translate
        virtIn = self.virtIn
        get.index.data ** virtIn.data[:PAGE_OFFSET_BITS]
        connect(virtIn.data, pageOffset.dataIn.data, fit=True)
        streamSync(masters=[virtIn],
                   slaves=[get.index, pageOffset.dataIn])

        # build translated addr from translated page addr and page offset
        physOut = self.physOut
        physOut.data ** Concat(get.item.data[:PAGE_OFFSET_BITS], pageOffset.dataOut.data)
        streamSync(masters=[get.item, pageOffset.dataOut],
                   slaves=[physOut])


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = MMU_1pageLvl()
    print(toRtl(u))
