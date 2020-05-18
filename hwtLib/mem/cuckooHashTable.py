#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, FsmBuilder, And, Or, If, ror, SwitchLogic, \
    connect, Concat
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.crcPoly import CRC_32, CRC_32C
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.mem.hashTable_intf import LookupKeyIntf, LookupResultIntf
from pycocotb.hdlSimulator import HdlSimulator
from hwt.serializer.simModel import SimModelSerializer
from pyMathBitPrecise.bit_utils import mask


class ORIGIN_TYPE():
    INSERT = 0
    LOOKUP = 1
    DELETE = 2


class CInsertIntf(HandshakeSync):

    def _config(self):
        self.KEY_WIDTH = Param(8)
        self.DATA_WIDTH = Param(0)

    def _declr(self):
        super(CInsertIntf, self)._declr()
        self.key = VectSignal(self.KEY_WIDTH)
        if self.DATA_WIDTH:
            self.data = VectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = CInsertIntfAgent(sim, self)


class CInsertIntfAgent(HandshakedAgent):
    """
    Agent for CInsertIntf interface
    """

    def __init__(self, sim, intf):
        HandshakedAgent.__init__(self, sim, intf)
        self._hasData = bool(intf.DATA_WIDTH)

    def get_data(self):
        intf = self.intf
        if self._hasData:
            return intf.key.read(), intf.data.read()
        else:
            return intf.key.read()

    def set_data(self, data):
        intf = self.intf
        if self._hasData:
            if data is None:
                k = None
                d = None
            else:
                k, d = data
            return intf.key.write(k), intf.data.write(d)
        else:
            return intf.key.write(data)


# https://web.stanford.edu/class/cs166/lectures/13/Small13.pdf
class CuckooHashTable(HashTableCore):
    """
    Cuckoo hash uses more tables with different hash functions

    Lookup is performed in all tables at once and if item is found in any
    table item is found otherwise item is not in tables.
    lookup time: O(1)

    Insert has to first lookup if item is in any table. If there is such a item
    it is replaced. If there is any empty element item is stored there.
    If there is a valid item under this key in all tables. One is selected
    and it is replaced by current item. Insert process then repeats with this item.

    Inserting into table does not have to be successful and in this case,
    fsm ends up in infinite loop and it will be reinserting items.

    .. aafig::
                    +-------------------------------------------+
                    |                                           |
                    |    CuckooHashTable                        |
        insert      |                                           |
        +--------------------------------------+  +---------+   |
                    |                          |  |         |   |
                    |                          v  v         |   | lookupRes
        lookup      |                        +-------+      +----------->
        +----------------------------------->|       |      |   |
                    |  +-------------------->| stash |      |   |
                    |  |                +----+       |      |   |
         delete     |  |                v    +------++      |   |
        +--------------+            +-------+       |       |   |
                    |               | insert|     lookup    |   |
                    |               +----+--+       v       |   |
                    |                 ^  |       +--------+ |   |
                    |                 |  +------>| tables | |   |
         clean      |   +--------+    |          +----+---+ |   |
        +-------------->|cleanFSM+ ---+               |     |   |
                    |   +--------+          lookupRes |     |   |
                    |                                 +-----+   |
                    +-------------------------------------------+

    .. hwt-schematic::
    """

    def __init__(self, polynomials=[CRC_32, CRC_32C]):
        """
        :param polynomials: list of polynomials for crc hashers used in tables
            for each item in this list table will be instantiated
        """
        super(HashTableCore, self).__init__()
        self.POLYNOMIALS = polynomials

    def _config(self):
        self.TABLE_SIZE = Param(32)
        self.DATA_WIDTH = Param(32)
        self.KEY_WIDTH = Param(8)
        self.LOOKUP_KEY = Param(False)

    def _declr(self):
        addClkRstn(self)
        self.TABLE_CNT = len(self.POLYNOMIALS)
        self.HASH_WITH = log2ceil(self.TABLE_SIZE)

        with self._paramsShared():
            self.insert = CInsertIntf()

            self.lookup = LookupKeyIntf()

            self.lookupRes = LookupResultIntf()._m()
            self.lookupRes.HASH_WIDTH = self.HASH_WITH

        with self._paramsShared(exclude=({"DATA_WIDTH"}, set())):
            self.delete = CInsertIntf()
            self.delete.DATA_WIDTH = 0

        self.clean = HandshakeSync()

        with self._paramsShared():
            self.tables = HObjList(HashTableCore(p) for p in self.POLYNOMIALS)
            for t in self.tables:
                t.ITEMS_CNT = self.TABLE_SIZE
                t.LOOKUP_HASH = True

    def cleanUpAddrIterator(self, en):
        lastAddr = self.TABLE_SIZE - 1
        addr = self._reg("cleanupAddr",
                         Bits(log2ceil(lastAddr), signed=False),
                         def_val=0)
        If(en,
           addr(addr + 1)
        )

        return addr, addr._eq(lastAddr)

    def insetOfTablesDriver(self, state, insertTargetOH, insertIndex,
                            stash):
        """
        :param state: state register of main fsm
        :param insertTargetOH: index of table where insert should be performed,
            one hot encoding
        :param insertIndex: address for table where item should be placed
        :param stash: stash register
        """
        fsm_t = state._dtype
        for i, t in enumerate(self.tables):
            ins = t.insert
            ins.hash(insertIndex)
            ins.key(stash.key)

            if self.DATA_WIDTH:
                ins.data(stash.data)
                ins.vld(Or(state._eq(fsm_t.cleaning),
                           state._eq(fsm_t.lookupResAck) & 
                           insertTargetOH[i]))
                ins.item_vld(stash.item_vld)

    def lookupResOfTablesDriver(self, resRead, resAck):
        """
        Controll lookupRes interface for each table
        """
        tables = self.tables
        # one hot encoded index where item should be stored (where was found
        # or where is place)
        targetOH = self._reg("targetOH", Bits(self.TABLE_CNT, force_vector=True))

        res = [t.lookupRes for t in tables]
        # synchronize all lookupRes from all tables
        StreamNode(masters=res).sync(resAck)

        insertFinal = self._reg("insertFinal")
        # select empty space or victim which which current insert item
        # should be swapped with
        lookupResAck = StreamNode(masters=[t.lookupRes for t in tables]).ack()
        lookupFoundOH = [t.lookupRes.found for t in tables]
        isEmptyOH = [~t.lookupRes.occupied for t in tables]
        _insertFinal = Or(*lookupFoundOH, *isEmptyOH)

        If(resRead & lookupResAck,
            If(Or(*lookupFoundOH),
                targetOH(Concat(*reversed(lookupFoundOH)))
            ).Else(
                SwitchLogic(
                    [(empty, targetOH(1 << i))
                     for i, empty in enumerate(isEmptyOH)],
                    default=If(targetOH != 0,
                                targetOH(ror(targetOH, 1))
                            ).Else(
                                targetOH(1 << (self.TABLE_CNT - 1))
                            )
                )
            ),
            insertFinal(_insertFinal)
        )
        return lookupResAck, insertFinal, lookupFoundOH, targetOH

    def insertAddrSelect(self, targetOH, state, cleanAddr):
        """
        Select a driver for insert address
        """
        insertIndex = self._sig("insertIndex", Bits(self.HASH_WITH))
        If(state._eq(state._dtype.cleaning),
            insertIndex(cleanAddr)
        ).Else(
            SwitchLogic([(targetOH[i],
                          insertIndex(t.lookupRes.hash))
                         for i, t in enumerate(self.tables)],
                        default=insertIndex(None))
        )
        return insertIndex

    def stashLoad(self, isIdle, stash):
        """
        load a stash register from lookup/insert/delete interface
        """
        lookup = self.lookup
        insert = self.insert
        delete = self.delete
        table_lookup_ack = StreamNode(slaves=[t.lookup for t in self.tables]).ack()
        lookup_in_progress = stash.origin_op._eq(ORIGIN_TYPE.LOOKUP)
        If(isIdle,
            If(self.clean.vld,
               stash.item_vld(0)
            ).Elif(delete.vld,
                stash.key(delete.key),
                stash.origin_op(ORIGIN_TYPE.DELETE),
                stash.item_vld(0),
            ).Elif(insert.vld,
                stash.origin_op(ORIGIN_TYPE.INSERT),
                stash.key(insert.key),
                stash.data(insert.data),
                stash.item_vld(1),
            ).Elif(table_lookup_ack & lookup.vld,
                stash.origin_op(ORIGIN_TYPE.LOOKUP),
                stash.key(lookup.key),
            ).Elif(table_lookup_ack,
                stash.origin_op(ORIGIN_TYPE.DELETE), # need to set something else than lookup
                stash.key(None),
            )
        )
        cmd_priority = [self.clean, self.delete, self.insert, lookup]
        for i, intf in enumerate(cmd_priority):
            withLowerPrio = cmd_priority[:i]
            rd = And(isIdle, *[~x.vld for x in withLowerPrio])
            if intf is lookup:
                rd = rd & (~lookup_in_progress |  # the stash not loaded yet
                    table_lookup_ack  # stash will be consummed
                )
            intf.rd(rd)

    def lookupOfTablesDriver(self, state, tableKey, lookop_en):
        for t in self.tables:
            t.lookup.key(tableKey)

        # activate lookup only in lookup state (for insert/delete) or if idle and processing lookups
        fsm_t = state._dtype
        en = state._eq(fsm_t.lookup) | (state._eq(fsm_t.idle) & lookop_en)
        StreamNode(slaves=[t.lookup for t in self.tables]).sync(en)

    def lookupResDriver(self, state, lookupFoundOH):
        """
        If lookup request comes from external interface "lookup" propagate results
        from tables to "lookupRes".
        """
        fsm_t = state._dtype
        lookupRes = self.lookupRes
        lookupResAck = StreamNode(masters=[t.lookupRes for t in self.tables]).ack()
        lookupRes.vld(state._eq(fsm_t.idle) & lookupResAck)

        SwitchLogic([(lookupFoundOH[i],
                      connect(t.lookupRes,
                              lookupRes,
                              exclude={lookupRes.vld,
                                       lookupRes.rd}))
                     for i, t in enumerate(self.tables)],
                    default=[
                        connect(self.tables[0].lookupRes,
                                lookupRes,
                                exclude={lookupRes.vld,
                                         lookupRes.rd})]
                    )

    def lookup_trans_cntr(self):
        # counter of pure lookup operations in progress
        lookup = self.lookup
        lookupRes = self.lookupRes
        lookup_in_progress = self._reg("lookup_in_progress", Bits(4), def_val=0)
        lookup_trans = lookup.rd & lookup.vld
        lookupRes_trans = lookupRes.rd & lookupRes.vld
        lookup_en = self._sig("lookup_en")
        If(lookup_en & lookup_trans & ~lookupRes_trans,
            lookup_in_progress(lookup_in_progress + 1)
        ).Elif(~lookup_trans & lookupRes_trans,
            lookup_in_progress(lookup_in_progress - 1)
        )
        return lookup_en, lookup_in_progress

    def _impl(self):
        propagateClkRstn(self)

        # stash is storage for item which is going to be swapped with actual
        stash_t = HStruct(
            (Bits(self.KEY_WIDTH), "key"),
            (Bits(self.DATA_WIDTH), "data"),
            (BIT, "item_vld"),
            (Bits(2), "origin_op"),
        )
        stash = self._reg("stash", stash_t, def_val={"origin_op": ORIGIN_TYPE.DELETE})

        cleanAck = self._sig("cleanAck")
        cleanAddr, cleanLast = self.cleanUpAddrIterator(cleanAck)
        lookupResRead = self._sig("lookupResRead")
        lookupResNext = self._sig("lookupResNext")
        (lookupResAck,
         insertFinal,
         lookupFound,
         targetOH) = self.lookupResOfTablesDriver(lookupResRead,
                                                  lookupResNext)
        tables = self.tables
        lookupAck = StreamNode(slaves=[t.lookup for t in tables]).ack()
        insertAck = StreamNode(slaves=[t.insert for t in tables]).ack()

        lookup_en, lookup_in_progress = self.lookup_trans_cntr()
        # lookup is not blocking and does not use fsm bellow
        # this fsm nadles only lookup for insert/delete
        fsm_t = HEnum("insertFsm_t", ["idle", "cleaning",
                                      "lookup", "lookupResWaitRd",
                                      "lookupResAck"])

        state = FsmBuilder(self, fsm_t, "insertFsm")\
            .Trans(fsm_t.idle,
                   # wait before lookup_in_progress reaches 0
                   # (new transactions should not be allowed if command has vld)
                   (lookup_in_progress._eq(0) & self.clean.vld, fsm_t.cleaning),
                   # before each insert suitable place has to be searched first
                   (lookup_in_progress._eq(0) & self.insert.vld | self.delete.vld, fsm_t.lookup)
            ).Trans(fsm_t.cleaning,
                # walk all items and clean it's item_vlds
                (cleanLast, fsm_t.idle)
            ).Trans(fsm_t.lookup,
                # search and resolve in which table item
                # should be stored
                (lookupAck, fsm_t.lookupResWaitRd)
            ).Trans(fsm_t.lookupResWaitRd,
                # process result of lookup and
                # write data stash to tables if
                # required
                (lookupResAck, fsm_t.lookupResAck)
            ).Trans(fsm_t.lookupResAck,
                # process lookupRes, if we are going to insert on place where
                # valid item is, it has to
                # be stored
                (stash.origin_op._eq(ORIGIN_TYPE.DELETE), fsm_t.idle),
                # insert into specified
                # table
                (insertAck & insertFinal, fsm_t.idle),
                (insertAck & ~insertFinal, fsm_t.lookup)
            ).stateReg
        lookup_en(state._eq(fsm_t.idle) & 
                  ~self.clean.vld & ~self.insert.vld & ~self.delete.vld & 
                  (lookup_in_progress != mask(lookup_in_progress._dtype.bit_length())))

        cleanAck(StreamNode(slaves=[t.insert for t in tables]).ack() & 
                 state._eq(fsm_t.cleaning))
        lookupResRead(state._eq(fsm_t.lookupResWaitRd))
        lookupResNext(state._eq(fsm_t.lookupResAck) | (state._eq(fsm_t.idle) & self.lookupRes.rd))

        isIdle = state._eq(fsm_t.idle)
        self.stashLoad(isIdle, stash)
        insertIndex = self.insertAddrSelect(targetOH, state, cleanAddr)
        self.insetOfTablesDriver(state, targetOH, insertIndex, stash)
        self.lookupResDriver(state, lookupFound)
        self.lookupOfTablesDriver(state, stash.key, stash.origin_op._eq(ORIGIN_TYPE.LOOKUP))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = CuckooHashTable([CRC_32, CRC_32])
    print(to_rtl_str(u))
