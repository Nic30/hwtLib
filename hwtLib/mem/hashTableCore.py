#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.code import Concat
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.unit import Unit
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.ramAsHs import RamHsR
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.hashTable_intf import LookupKeyIntf, HashTableIntf


# https://web.stanford.edu/class/cs166/lectures/13/Small13.pdf
class HashTableCore(Unit):
    """
    Generic hash table, in block RAM
    there is a input key which is hashed ad this has is used as an index into memory
    item on this place is checked and returned on "lookupRes" interface
    (item does have to be found, see "found" flag in LookupResultIntf)

    memory is an array of items in format

    .. code-block:: c

        struct item {
            bool item_vld;
            data_t data;
            key_t key;
        };

    :ivar ~.ITEMS_CNT: number of items in memory of hash table
    :ivar ~.KEY_WIDTH: width of the key used by hash table
    :ivar ~.DATA_WIDTH: width of data, can be zero and then no data
        interface is instantiated
    :ivar ~.LOOKUP_ID_WIDTH: width of id signal for lookup (tag used only
        by parent component to mark this lookup for later result processing,
        can be 0)
    :ivar ~.LOOKUP_HASH: flag if lookup interface should have hash signal
    :ivar ~.LOOKUP_KEY: flag if lookup interface should have key signal
    :ivar ~.POLYNOME: polynome for crc hash used in this table

    .. figure:: ./_static/HashTableCore.png

    .. hwt-autodoc:: _example_HashTableCore
    """

    def __init__(self, polynome):
        super(HashTableCore, self).__init__()
        self.POLYNOME = polynome

    def _config(self):
        HashTableIntf._config(self)

    def _declr_common(self):
        addClkRstn(self)
        with self._paramsShared():
            self.io = HashTableIntf()

        h = self.hash = CrcComb()
        h.DATA_WIDTH = self.KEY_WIDTH
        h.setConfig(self.POLYNOME)

    def _declr(self):
        self._declr_common()
        self.r = RamHsR()._m()
        self.w = AddrDataHs()._m()
        for i in [self.r, self.w]:
            i.ADDR_WIDTH = log2ceil(self.ITEMS_CNT)
            i.DATA_WIDTH = self.KEY_WIDTH + self.DATA_WIDTH + 1  # +1 for item_vld

    def parseItem(self, sig):
        """
        Parse data stored in hash table
        """
        DW = self.DATA_WIDTH
        KW = self.KEY_WIDTH

        item_vld = sig[0]

        dataLow = 1
        dataHi = dataLow + DW
        if dataHi > dataLow:
            data = sig[dataHi:dataLow]
        else:
            data = None

        keyLow = dataHi
        keyHi = keyLow + KW
        # assert keyHi > keyLow

        key = sig[keyHi:keyLow]

        return (key, data, item_vld)

    def lookupLogic(self, ramR: RamHsR):
        h = self.hash
        lookup = self.io.lookup
        res = self.io.lookupRes

        # tmp storage for original key and hash for later check
        origKeyIn = LookupKeyIntf()
        origKeyIn.KEY_WIDTH = self.KEY_WIDTH
        self.origKeyIn = origKeyIn

        origKeyIn.key(lookup.key)
        if lookup.LOOKUP_ID_WIDTH:
            origKeyIn.lookupId(lookup.lookupId)
        origKey = HsBuilder(self, origKeyIn).buff(2).end

        # hash key and address with has in table
        h.dataIn(lookup.key)
        # hash can be wider
        ramR.addr.data(h.dataOut, fit=True)

        inputSlaves = [ramR.addr, origKeyIn]
        outputMasters = [origKey, ramR.data, ]

        if self.LOOKUP_HASH:
            origHashIn = Handshaked()
            origHashIn.DATA_WIDTH = self.io.HASH_WIDTH
            self.origHashIn = origHashIn
            origHashOut = HsBuilder(self, origHashIn).buff(2).end

            origHashIn.data(h.dataOut, fit=True)

            inputSlaves.append(origHashIn)
            outputMasters.append(origHashOut)

        StreamNode(masters=[lookup],
                   slaves=inputSlaves).sync()

        # propagate loaded data
        StreamNode(masters=outputMasters,
                   slaves=[res]).sync()

        key, data, item_vld = self.parseItem(ramR.data.data)

        if self.LOOKUP_HASH:
            res.hash(origHashOut.data)

        if self.LOOKUP_KEY:
            res.key(key)

        if self.LOOKUP_ID_WIDTH:
            res.lookupId(origKey.lookupId)

        if self.DATA_WIDTH:
            res.data(data)
        res.occupied(item_vld)
        res.found(origKey.key._eq(key) & item_vld)

    def insertLogic(self, ramW: AddrDataHs):
        In = self.io.insert

        if self.DATA_WIDTH:
            rec = Concat(In.key, In.data, In.item_vld)
        else:
            rec = Concat(In.key, In.item_vld)

        ramW.data(rec)
        ramW.addr(In.hash)
        StreamNode(masters=[In], slaves=[ramW]).sync()

    def _impl(self, r: Optional[RamHsR]=None, w: Optional[AddrDataHs]=None):
        if r is None:
            r = self.r
        if w is None:
            w = self.w

        self.lookupLogic(r)
        self.insertLogic(w)
        propagateClkRstn(self)


def _example_HashTableCore():
    return HashTableCore(CRC_32)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HashTableCore()
    print(to_rtl_str(u))
