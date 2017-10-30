#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, Concat, Switch, isPow2
from hwt.hdl.typeShortcuts import vec
from hwt.interfaces.std import Handshaked, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.amba.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode


class ArrayItemGetter(Unit):
    """
    Get specific item from array by index
    """
    def _config(self):
        self.ITEMS = Param(32)
        self.ITEM_WIDTH = Param(32)
        self.ID = Param(0)
        self.ID_WIDTH = Param(4)
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(32)
        self.MAX_TRANS_OVERLAP = Param(16)

    def _declr(self):
        addClkRstn(self)
        # addr of start of array
        self.base = VectSignal(self.ADDR_WIDTH)

        # input index of item to get
        self.index = Handshaked()
        self.index.DATA_WIDTH.set(log2ceil(self.ITEMS))

        # output item from array
        self.item = Handshaked()
        self.item.DATA_WIDTH.set(self.ITEM_WIDTH)

        self.ITEMS_IN_DATA_WORD = int(self.DATA_WIDTH) // int(self.ITEM_WIDTH)

        with self._paramsShared():
            # interface for communication with datapump
            self.rDatapump = AxiRDatapumpIntf()
            self.rDatapump.MAX_LEN.set(1)

        if self.ITEMS_IN_DATA_WORD > 1:
            assert isPow2(self.ITEMS_IN_DATA_WORD)
            f = self.itemSubIndexFifo = HandshakedFifo(Handshaked)
            f.DATA_WIDTH.set(log2ceil(self.ITEMS_IN_DATA_WORD))
            f.DEPTH.set(self.MAX_TRANS_OVERLAP)

    def _impl(self):
        propagateClkRstn(self)
        ITEM_WIDTH = int(self.ITEM_WIDTH)
        DATA_WIDTH = int(self.DATA_WIDTH)
        ITEMS_IN_DATA_WORD = self.ITEMS_IN_DATA_WORD
        ITEM_SIZE_IN_WORDS = 1

        if ITEM_WIDTH % 8 != 0 or ITEM_SIZE_IN_WORDS * DATA_WIDTH != ITEMS_IN_DATA_WORD * ITEM_WIDTH:
            raise NotImplementedError(ITEM_WIDTH)

        req = self.rDatapump.req
        req.id(self.ID)
        req.len(ITEM_SIZE_IN_WORDS - 1)
        req.rem(0)

        if ITEMS_IN_DATA_WORD == 1:
            addr = Concat(self.index.data, vec(0, log2ceil(ITEM_WIDTH // 8)))
            req.addr(self.base + fitTo(addr, req.addr))
            StreamNode(masters=[self.index], slaves=[req]).sync()

            self.item.data(self.rDatapump.r.data)
            StreamNode(masters=[self.rDatapump.r], slaves=[self.item]).sync()

        else:
            r = self.rDatapump.r.data
            f = self.itemSubIndexFifo
            subIndexBits = f.dataIn.data._dtype.bit_length()
            itemAlignBits = log2ceil(ITEM_WIDTH // 8)
            addr = Concat(self.index.data[:subIndexBits],
                          vec(0, itemAlignBits + subIndexBits))

            req.addr(self.base + fitTo(addr, req.addr))
            f.dataIn.data(self.index.data[subIndexBits:])
            StreamNode(masters=[self.index],
                       slaves=[req, f.dataIn]).sync()

            Switch(f.dataOut.data).addCases([
                (ITEMS_IN_DATA_WORD - i - 1, self.item.data(r[(ITEM_WIDTH * (i + 1)): (ITEM_WIDTH * i)]))
                for i in range(ITEMS_IN_DATA_WORD)
                ])
            StreamNode(masters=[self.rDatapump.r, f.dataOut],
                       slaves=[self.item]).sync()


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = ArrayItemGetter()
    print(toRtl(u))
