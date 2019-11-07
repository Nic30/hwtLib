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
from hwt.synthesizer.param import Param
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.mem.hashTable_intf import LookupKeyIntf, LookupResultIntf
from hwtLib.logic.crcPoly import CRC_32, CRC_32C
from hwt.synthesizer.hObjList import HObjList
from pycocotb.hdlSimulator import HdlSimulator


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
                    | CuckooHashTable                           |
        insert      |                                           |
        +--------------------------------------+ +----------+   |
                    |                          | |          |   | lookupRes
        lookup      |                        +-v-v---+      +----------->
        +------------------------------------>       |      |   |
                    |  +---------------------> stash |      |   |
                    |  |               +-----+       |      |   |
         delete     |  |               |     +---+---+      |   |
        +--------------+           +---v---+     |          |   |
                    |              | insert|  lookup        |   |
         clean      |  +--------+  +-^--+--+     |          |   |
        +-------------->cleanFSM+----+  |    +---v----+     |   |
                    |  +--------+       +----> tables |     |   |
                    |                        +--------+     |   |
                    |                         lookupRes     |   |
                    |                            +----------+   |
                    |                                           |
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
                            stash, isExternLookup):
        """
        :param state: state register of main fsm
        :param insertTargetOH: index of table where insert should be performed,
            one hot encoding
        :param insertIndex: address for table where item should be placed
        :param stash: stash register
        :param isExternLookup: flag for lookup initialized by external
            "lookup" interface
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
                           insertTargetOH[i] &
                           ~isExternLookup))
                ins.vldFlag(stash.vldFlag)

    def lookupResOfTablesDriver(self, resRead, resAck):
        tables = self.tables
        # one hot encoded index where item should be stored (where was found
        # or where is place)
        targetOH = self._reg("targetOH", Bits(self.TABLE_CNT))

        res = list(map(lambda t: t.lookupRes, tables))
        # synchronize all lookupRes from all tables
        StreamNode(masters=res).sync(resAck)

        insertFinal = self._reg("insertFinal")
        # select empty space or victim which which current insert item
        # should be swapped with
        lookupResAck = StreamNode(masters=map(
            lambda t: t.lookupRes, tables)).ack()
        insertFoundOH = list(map(lambda t: t.lookupRes.found, tables))
        isEmptyOH = list(map(lambda t: ~t.lookupRes.occupied, tables))
        _insertFinal = Or(*insertFoundOH, *isEmptyOH)

        If(resRead & lookupResAck,
            If(Or(*insertFoundOH),
                targetOH(Concat(*reversed(insertFoundOH)))
            ).Else(
                SwitchLogic([(empty, targetOH(1 << i))
                             for i, empty in enumerate(isEmptyOH)
                             ],
                            default=If(targetOH,
                                       targetOH(ror(targetOH, 1))
                                       ).Else(
                    targetOH(1 << (self.TABLE_CNT - 1))
                ))
            ),
            insertFinal(_insertFinal)
           )
        return lookupResAck, insertFinal, insertFoundOH, targetOH

    def insertAddrSelect(self, targetOH, state, cleanAddr):
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

    def stashLoad(self, isIdle, stash, lookupOrigin_out):
        lookup = self.lookup
        insert = self.insert
        delete = self.delete
        If(isIdle,
            If(self.clean.vld,
               stash.vldFlag(0)
            ).Elif(delete.vld,
                stash.key(delete.key),
                lookupOrigin_out(ORIGIN_TYPE.DELETE),
                stash.vldFlag(0),
            ).Elif(insert.vld,
                lookupOrigin_out(ORIGIN_TYPE.INSERT),
                stash.key(insert.key),
                stash.data(insert.data),
                stash.vldFlag(1),
            ).Elif(lookup.vld,
                lookupOrigin_out(ORIGIN_TYPE.LOOKUP),
                stash.key(lookup.key),
            )
        )
        priority = [self.clean, self.delete, self.insert, lookup]
        for i, intf in enumerate(priority):
            withLowerPrio = priority[:i]
            intf.rd(And(isIdle, *map(lambda x: ~x.vld, withLowerPrio)))

    def lookupOfTablesDriver(self, state, tableKey):
        fsm_t = state._dtype
        for t in self.tables:
            t.lookup.key(tableKey)

        # activate lookup only in lookup state
        en = state._eq(fsm_t.lookup)
        StreamNode(slaves=[t.lookup for t in self.tables]).sync(en)

    def lookupResDriver(self, state, lookupOrigin, lookupAck, insertFoundOH):
        """
        If lookup request comes from external interface "lookup" propagate results
        from tables to "lookupRes".
        """
        fsm_t = state._dtype
        lookupRes = self.lookupRes
        lookupRes.vld(state._eq(fsm_t.lookupResAck) & 
                      lookupOrigin._eq(ORIGIN_TYPE.LOOKUP) & 
                      lookupAck)

        SwitchLogic([(insertFoundOH[i],
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

    def _impl(self):
        propagateClkRstn(self)
        lookupRes = self.lookupRes
        tables = self.tables

        # stash is storage for item which is going to be swapped with actual
        stash_t = HStruct(
            (Bits(self.KEY_WIDTH), "key"),
            (Bits(self.DATA_WIDTH), "data"),
            (BIT, "vldFlag")
        )
        stash = self._reg("stash", stash_t)
        lookupOrigin = self._reg("lookupOrigin", Bits(2))

        cleanAck = self._sig("cleanAck")
        cleanAddr, cleanLast = self.cleanUpAddrIterator(cleanAck)
        lookupResRead = self._sig("lookupResRead")
        lookupResNext = self._sig("lookupResNext")
        (lookupResAck,
         insertFinal,
         insertFound,
         targetOH) = self.lookupResOfTablesDriver(lookupResRead,
                                                  lookupResNext)
        lookupAck = StreamNode(slaves=map(lambda t: t.lookup, tables)).ack()
        insertAck = StreamNode(slaves=map(lambda t: t.insert, tables)).ack()

        fsm_t = HEnum("insertFsm_t", ["idle", "cleaning",
                                      "lookup", "lookupResWaitRd",
                                      "lookupResAck"])

        isExternLookup = lookupOrigin._eq(ORIGIN_TYPE.LOOKUP)
        state = FsmBuilder(self, fsm_t, "insertFsm")\
            .Trans(fsm_t.idle,
                   (self.clean.vld, fsm_t.cleaning),
                   # before each insert suitable place has to be searched first
                   (self.insert.vld | self.lookup.vld | 
                    self.delete.vld, fsm_t.lookup)
            ).Trans(fsm_t.cleaning,
                # walk all items and clean it's vldFlags
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
                (lookupOrigin._eq(
                    ORIGIN_TYPE.DELETE), fsm_t.idle),
                (isExternLookup & 
                 lookupRes.rd, fsm_t.idle),
                # insert into specified
                # table
                (~isExternLookup & insertAck & 
                 insertFinal, fsm_t.idle),
                (~isExternLookup & insertAck & 
                 ~insertFinal, fsm_t.lookup)
            ).stateReg

        cleanAck(StreamNode(slaves=[t.insert for t in tables]).ack() & 
                 state._eq(fsm_t.cleaning))
        lookupResRead(state._eq(fsm_t.lookupResWaitRd))
        lookupResNext(And(state._eq(fsm_t.lookupResAck),
                          Or(lookupOrigin != ORIGIN_TYPE.LOOKUP, lookupRes.rd)))

        isIdle = state._eq(fsm_t.idle)
        self.stashLoad(isIdle, stash, lookupOrigin)
        insertIndex = self.insertAddrSelect(targetOH, state, cleanAddr)
        self.insetOfTablesDriver(
            state, targetOH, insertIndex, stash, isExternLookup)
        self.lookupResDriver(state, lookupOrigin, lookupAck, insertFound)
        self.lookupOfTablesDriver(state, stash.key)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = CuckooHashTable([CRC_32, CRC_32])
    print(toRtl(u))
