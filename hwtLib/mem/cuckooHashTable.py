from hwt.code import log2ceil, FsmBuilder, And, Or, If, Switch, ror, SwitchLogic,\
    connect, Concat, In
from hwt.interfaces.std import VectSignal, Handshaked, HandshakeSync
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.mem.hashTable_intf import LookupKeyIntf, LookupResultIntf
from hwtLib.handshaked.builder import HsBuilder
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwtLib.handshaked.streamNode import streamAck, streamSync
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.defs import BIT


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


# https://web.stanford.edu/class/cs166/lectures/13/Small13.pdf
class CuckooHashTableCore(HashTableCore):
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

    """

    def __init__(self, polynomials):
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

    def _declr(self):
        addClkRstn(self)
        self.TABLE_CNT = len(self.POLYNOMIALS)
        self.HASH_WITH = log2ceil(self.TABLE_SIZE).val

        with self._paramsShared():
            self.insert = CInsertIntf()

            self.lookup = LookupKeyIntf()

            self.lookupRes = LookupResultIntf()
            self.lookupRes.HASH_WIDTH.set(self.HASH_WITH)
        self.clean = HandshakeSync()

        self.tables = [HashTableCore(p) for p in self.POLYNOMIALS]
        with self._paramsShared():
            self._registerArray("table", self.tables)
            for t in self.tables:
                t.ITEMS_CNT.set(self.TABLE_SIZE)

    def cleanUpAddrIterator(self, en):
        lastAddr = self.TABLE_SIZE - 1
        addr = self._reg("cleanupAddr",
                         vecT(log2ceil(lastAddr), signed=False),
                         defVal=0)
        If(en,
           addr ** (addr + 1)
        )

        return addr, addr._eq(lastAddr)

    def insetOfTablesDriver(self, insertTargetOH, stash):
        """
        :param insertTargetOH: index of table where insert should be performed,
            one hot encoding
        """

        for i, t in enumerate(self.tables):
            t.insert.key ** stash.key
            if self.DATA_WIDTH:
                t.insert.data ** stash.data

        for t in self.tables:
            ins = t.insert
            ins.hash ** stash.hash
            ins.key ** stash.key

            if self.DATA_WIDTH:
                ins.data ** stash.data
                ins.vld ** insertTargetOH[i]
                ins.vldFlag ** stash.vldFlag

    def lookupResOfTablesDriver(self, resRead, resAck, insertTargetOH_out):
        tables = self.tables
        res = list(map(lambda t: t.lookupRes, tables))
        # synchronize all lookupRes from all tables
        streamSync(masters=res, extraConds={lr: resAck for lr in res})

        insertFinal = self._reg("insertFinal")
        # select empty space or victim witch which current insert item
        # should be swapped with
        lookupResAck = streamAck(masters=map(lambda t: t.lookupRes, tables))
        insertFoundOH = list(map(lambda t: t.lookupRes.found, tables))
        isEmptyOH = list(map(lambda t: ~t.lookupRes.occupied, tables))
        _insertFinal = Or(*insertFoundOH, *isEmptyOH)

        If(resRead & lookupResAck,
            If(Or(*insertFoundOH),
                insertTargetOH_out ** Concat(*insertFoundOH)
            ).Elif(Or(*isEmptyOH),
                insertTargetOH_out ** Concat(*isEmptyOH)
            ).Else(
                # [TODO] assert has only one 1
                If(insertTargetOH_out,
                   insertTargetOH_out ** ror(insertTargetOH_out, 1)
                ).Else(
                   insertTargetOH_out ** (1 << (self.TABLE_CNT - 1))
                )
            ),
            insertFinal ** _insertFinal
        )
        return lookupResAck, insertFinal, insertFoundOH

    def insertCore(self):
        """
        Insert core has register which contains value which should be inserted

        lookup,
        look
        """
        lookup = self.lookup
        lookupRes = self.lookupRes
        insert = self.insert
        tables = self.tables

        # stash is storage for item which is going to be swapped with actual
        stash_t = HStruct(
            (vecT(self.KEY_WIDTH), "key"),
            (vecT(self.DATA_WIDTH), "data"),
            )
        stash = self._reg("stash", stash_t)

        targetOH = self._reg("targetOH", vecT(self.TABLE_CNT))
        lookupOrigin = self._reg("lookupOrigin", vecT(2))
        # specifies if current data are from outside or it is reinserting

        cleanAck = self._sig("cleanAck")
        cleanAddr, cleanLast = self.cleanUpAddrIterator(cleanAck)

        collectLookupRes_en = self._sig("collectLookupRes_en")
        (lookupResAck,
         insertFinal,
         insertFound) = self.lookupResOfTablesDriver(collectLookupRes_en,
                                                     targetOH,
                                                     tmpHash)
        lookupAck = streamAck(slaves=map(lambda t: t.lookup, tables))

        insertAck = streamAck(slaves=map(lambda t: t.insert, tables))

        fsm_t = Enum("insertFsm_t", ["idle", "cleaning",
                                     "lookup", "lookupResWaitRd", "lookupResAck"])

        isExternLookup = lookupOrigin._eq(ORIGIN_TYPE.LOOKUP)
        state = FsmBuilder(self, fsm_t, "insertFsm")\
            .Trans(fsm_t.idle,
                   (self.clean.vld, fsm_t.cleaning),
                   # before each insert suitable place has to be searched first
                   (self.insert.vld | lookup.vld, fsm_t.lookup)
            ).Trans(fsm_t.cleaning,
                    # walk all items and clean it's vldFlags
                    (cleanLast, fsm_t.idle)
            ).Trans(fsm_t.lookup,
                    # search and resolve in which table item should be stored
                    (lookupAck, fsm_t.insert)
            ).Trans(fsm_t.lookupResWaitRd,
                    
            ).Trans(fsm_t.lookupResAck,
                    # process lookupRes, if we are going to insert on place where
                    # valid item is, it has to be stored
                    (isExternLookup & lookupRes.rd, fsm_t.lookupResAck),
                    # insert into specified table
                    (~isExternLookup & insertAck & insertFinal, fsm_t.idle),
                    (~isExternLookup & insertAck & ~insertFinal, fsm_t.lookup)
            ).stateReg

        cleanAck ** (streamAck(slaves=[t.insert for t in tables]) &
                     state._eq(fsm_t.cleaning))
        collectLookupRes_en ** And(state._eq(fsm_t.lookupRes),
                                   Or(lookupOrigin != ORIGIN_TYPE.LOOKUP, lookupRes.rd))
        If(collectLookupRes_en & lookupAck,
           insertOrigin ** lookupOrigin
        )

        isIdle = state._eq(fsm_t.idle)
        self.clean.rd ** isIdle
        If(isIdle,
            If(insert.vld,
               lookupOrigin ** ORIGIN_TYPE.INSERT,
               stash.key ** insert.key,
               stash.data ** insert.data,
               stash.vldFlag ** 1,
            ).Elif(lookup.vld,
               lookupOrigin ** ORIGIN_TYPE.LOOKUP,
               stash.key ** lookup.key,
            )
        )

        insert.rd ** (isIdle & ~self.clean.vld)

        self.insetOfTablesDriver(targetOH, stash)
        self.lookupResDriver(state, lookupOrigin, lookupAck, insertFound)
        self.lookupOfTablesDriver(state, tmpKey, lookupOrigin)

    def lookupOfTablesDriver(self, state, tmpKey, lookupOrigin):
        fsm_t = state._dtype
        for t in self.tables:
            t.lookup.key ** tmpKey

        # activate lookup only in lookup state
        en = state._eq(fsm_t.lookup)
        extraConds = {self.lookup: en}
        for t in self.tables:
            extraConds[t.lookup] = en

        streamSync(masters=[self.lookup],
                   slaves=[t.lookup for t in self.tables],
                   extraConds=extraConds,
                   # ignore self.lookup when it is just internal lookup
                   # and not lookup request itself
                   skipWhen={self.lookup: lookupOrigin != ORIGIN_TYPE.LOOKUP})

    def lookupResDriver(self, state, lookupOrigin, lookupAck, insertFoundOH):
        """
        If lookup request comes from external interface "lookup" propagate results
        from tables to "lookupRes".
        """
        fsm_t = state._dtype
        lookupRes = self.lookupRes
        lookupRes.vld ** (state._eq(fsm_t.lookupRes) &
                          lookupOrigin._eq(ORIGIN_TYPE.LOOKUP) &
                          lookupAck)

        SwitchLogic([(insertFoundOH[i],
                      connect(t.lookupRes,
                              lookupRes,
                              exclude={lookupRes.vld,
                                       lookupRes.rd}))
                     for i, t in enumerate(self.tables)])

    def _impl(self):
        propagateClkRstn(self)
        self.insertCore()


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.logic.crcPoly import CRC_32
    u = CuckooHashTableCore([CRC_32, CRC_32])
    print(toRtl(u))
