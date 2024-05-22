#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtLib.handshaked.ramAsAddrDataRdVld import RamAsAddrDataRdVld
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.mem.ram import RamSingleClock


class HashTableCoreWithRam(HashTableCore):
    """
    :see: :class:`~.HashTableCore`

    .. hwt-autodoc:: _example_HashTableCoreWithRam
    """

    @override
    def hwDeclr(self):
        HashTableCoreWithRam._declr_common(self)
        t = self.table = RamSingleClock()
        t.PORT_CNT = 1
        t.ADDR_WIDTH = log2ceil(self.ITEMS_CNT)
        t.DATA_WIDTH = self.KEY_WIDTH + self.DATA_WIDTH + 1  # +1 for item_vld

        tc = self.tableConnector = RamAsAddrDataRdVld()
        tc.ADDR_WIDTH = t.ADDR_WIDTH
        tc.DATA_WIDTH = t.DATA_WIDTH

    @override
    def hwImpl(self, r=None, w=None):
        table = self.tableConnector
        self.table.port[0](table.ram)
        HashTableCore.hwImpl(self, r=table.r, w=table.w)


def _example_HashTableCoreWithRam():
    return HashTableCoreWithRam(CRC_32)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_HashTableCoreWithRam()
    print(to_rtl_str(m))
