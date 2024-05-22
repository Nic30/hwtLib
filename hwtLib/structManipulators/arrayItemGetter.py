#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, Switch
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil, isPow2
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.amba.datapump.intf import HwIOAxiRDatapump
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode


class ArrayItemGetter(HwModule):
    """
    Get specific item from array by index

    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        self.ITEMS = HwParam(32)
        self.ITEM_WIDTH = HwParam(32)
        self.ID = HwParam(0)
        self.ID_WIDTH = HwParam(4)
        self.DATA_WIDTH = HwParam(64)
        self.ADDR_WIDTH = HwParam(32)
        self.MAX_TRANS_OVERLAP = HwParam(16)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        # addr of start of array
        self.base = HwIOVectSignal(self.ADDR_WIDTH)

        # input index of item to get
        self.index = HwIODataRdVld()
        self.index.DATA_WIDTH = log2ceil(self.ITEMS)

        # output item from array
        self.item = HwIODataRdVld()._m()
        self.item.DATA_WIDTH = self.ITEM_WIDTH

        self.ITEMS_IN_DATA_WORD = int(self.DATA_WIDTH) // int(self.ITEM_WIDTH)

        with self._hwParamsShared():
            # interface for communication with datapump
            self.rDatapump = HwIOAxiRDatapump()._m()
            self.rDatapump.MAX_BYTES = self.DATA_WIDTH // 8

        if self.ITEMS_IN_DATA_WORD > 1:
            assert isPow2(self.ITEMS_IN_DATA_WORD)
            f = self.itemSubIndexFifo = HandshakedFifo(HwIODataRdVld)
            f.DATA_WIDTH = log2ceil(self.ITEMS_IN_DATA_WORD)
            f.DEPTH = self.MAX_TRANS_OVERLAP

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        ITEM_WIDTH = int(self.ITEM_WIDTH)
        DATA_WIDTH = int(self.DATA_WIDTH)
        ITEMS_IN_DATA_WORD = self.ITEMS_IN_DATA_WORD
        ITEM_SIZE_IN_WORDS = 1

        if ITEM_WIDTH % 8 != 0 or ITEM_SIZE_IN_WORDS * DATA_WIDTH != ITEMS_IN_DATA_WORD * ITEM_WIDTH:
            raise NotImplementedError(ITEM_WIDTH)

        req = self.rDatapump.req
        req.id(self.ID)
        req.rem(0)

        if ITEMS_IN_DATA_WORD == 1:
            addr = Concat(self.index.data, HBits(log2ceil(ITEM_WIDTH // 8)).from_py(0))
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
                          HBits(itemAlignBits + subIndexBits).from_py(0))

            req.addr(self.base + fitTo(addr, req.addr))
            f.dataIn.data(self.index.data[subIndexBits:])
            StreamNode(masters=[self.index],
                       slaves=[req, f.dataIn]).sync()

            Switch(f.dataOut.data).add_cases([
                (i, self.item.data(r[(ITEM_WIDTH * (i + 1)):(ITEM_WIDTH * i)]))
                for i in range(ITEMS_IN_DATA_WORD)
                ])
            StreamNode(masters=[self.rDatapump.r, f.dataOut],
                       slaves=[self.item]).sync()


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = ArrayItemGetter()
    print(to_rtl_str(m))
