#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, connect, Concat
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.handshaked.ramAsHs import RamAsHs
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.hashTable_intf import InsertIntf, LookupKeyIntf, \
    LookupResultIntf
from hwtLib.mem.ram import RamSingleClock
from hwtLib.handshaked.builder import HsBuilder


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
    :ivar ~.LOOKUP_HASH: flag if this interface should have hash signal
    :ivar ~.LOOKUP_KEY: flag if this interface should have key signal
    :ivar ~.POLYNOME: polynome for crc hash used in this table

    .. aafig::

        insert   +-----------+
        -------->|           | lookupRes
        lookup   | HashTable +---------->
        -------->|           |
                 +-----------+

    .. hwt-schematic:: _example_HashTableCore

    """

    def __init__(self, polynome):
        super(HashTableCore, self).__init__()
        self.POLYNOME = polynome

    def _config(self):
        self.ITEMS_CNT = Param(32)
        self.KEY_WIDTH = Param(16)
        self.DATA_WIDTH = Param(8)
        self.LOOKUP_ID_WIDTH = Param(0)
        self.LOOKUP_HASH = Param(False)
        self.LOOKUP_KEY = Param(False)

    def _declr(self):
        addClkRstn(self)
        assert int(self.KEY_WIDTH) > 0
        assert int(self.DATA_WIDTH) >= 0
        assert int(self.ITEMS_CNT) > 1

        self.HASH_WIDTH = log2ceil(self.ITEMS_CNT)

        assert self.HASH_WIDTH < int(self.KEY_WIDTH), (
            "It makes no sense to use hash table when you can use key directly as index",
            self.HASH_WIDTH, self.KEY_WIDTH)

        with self._paramsShared():
            self.insert = InsertIntf()
            self.insert.HASH_WIDTH = self.HASH_WIDTH

            self.lookup = LookupKeyIntf()

            self.lookupRes = LookupResultIntf()._m()
            self.lookupRes.HASH_WIDTH = self.HASH_WIDTH

        t = self.table = RamSingleClock()
        t.PORT_CNT = 1
        t.ADDR_WIDTH = log2ceil(self.ITEMS_CNT)
        t.DATA_WIDTH = self.KEY_WIDTH + self.DATA_WIDTH + 1  # +1 for item_vld

        tc = self.tableConnector = RamAsHs()
        tc.ADDR_WIDTH = t.ADDR_WIDTH
        tc.DATA_WIDTH = t.DATA_WIDTH

        h = self.hash = CrcComb()
        h.DATA_WIDTH = self.KEY_WIDTH
        h.setConfig(self.POLYNOME)

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

    def lookupLogic(self, ramR):
        h = self.hash
        lookup = self.lookup
        res = self.lookupRes

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
        connect(h.dataOut, ramR.addr.data, fit=True)

        inputSlaves = [ramR.addr, origKeyIn]
        outputMasters = [origKey, ramR.data, ]

        if self.LOOKUP_HASH:
            origHashIn = Handshaked()
            origHashIn.DATA_WIDTH = self.HASH_WIDTH
            self.origHashIn = origHashIn
            origHashOut = HsBuilder(self, origHashIn).buff(2).end

            connect(h.dataOut, origHashIn.data, fit=True)

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
            res.key(origKey.key)

        if self.LOOKUP_ID_WIDTH:
            res.lookupId(origKey.lookupId)

        if self.DATA_WIDTH:
            res.data(data)
        res.occupied(item_vld)
        res.found(origKey.key._eq(key) & item_vld)

    def insertLogic(self, ramW):
        In = self.insert

        if self.DATA_WIDTH:
            rec = Concat(In.key, In.data, In.item_vld)
        else:
            rec = Concat(In.key, In.item_vld)

        ramW.data(rec)
        ramW.addr(In.hash)
        StreamNode(masters=[In], slaves=[ramW]).sync()

    def _impl(self):
        propagateClkRstn(self)

        table = self.tableConnector
        self.table.port[0](table.ram)
        self.lookupLogic(table.r)
        self.insertLogic(table.w)


def _example_HashTableCore():
    return HashTableCore(CRC_32)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HashTableCore()
    print(to_rtl_str(u))
