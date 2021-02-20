#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import FsmBuilder, And, Or, If, ror, SwitchLogic, \
    Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import HandshakeSync
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.cuckooHashTable_intf import CInsertIntf, CInsertResIntf
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.mem.hashTable_intf import LookupKeyIntf, LookupResultIntf, \
    HashTableIntf


ORIGIN_TYPE = HEnum("ORIGIN_TYPE", ["INSERT", "LOOKUP", "DELETE"])


# https://web.stanford.edu/class/cs166/lectures/13/Small13.pdf
class CuckooHashTable(HashTableCore):
    """
    Cuckoo hash uses more tables with different hash functions

    Lookup is performed in all tables at once and if item is found in any
    table. The item is found. Otherwise item is not in tables.
    lookup time: O(1)

    Insert has to first lookup if item is in any table. If any table contains invalid item.
    The item is stored there and insert operation is complete.
    If there was a valid item under this key in all tables. One is selected
    and it is swapped with current item. Insert process then repeats with this item.
    Until some invalid item (empty slot) is found.

    Inserting into table does not have to be successful and in this case,
    fsm ends up in infinite loop and it will be reinserting items for ever.
    insert time: O(inf)

    .. figure:: ./_static/CuckooHashTable.png

    .. hwt-autodoc::
    """

    def __init__(self):
        Unit.__init__(self)

    def _config(self):
        self.TABLE_SIZE = Param(32)
        self.DATA_WIDTH = Param(32)
        self.KEY_WIDTH = Param(8)
        self.LOOKUP_KEY = Param(False)
        self.TABLE_CNT = Param(2)
        self.MAX_LOOKUP_OVERLAP = Param(16)
        self.MAX_REINSERT = Param(15)

    def _declr_outer_io(self):
        addClkRstn(self)
        assert self.TABLE_SIZE % self.TABLE_CNT == 0
        self.HASH_WIDTH = log2ceil(self.TABLE_SIZE // self.TABLE_CNT)

        with self._paramsShared():
            self.insert = CInsertIntf()
            self.insertRes = CInsertResIntf()._m()
            self.lookup = LookupKeyIntf()
            self.lookupRes = LookupResultIntf()._m()
            self.lookupRes.HASH_WIDTH = self.HASH_WIDTH

        with self._paramsShared(exclude=({"DATA_WIDTH"}, set())):
            self.delete = CInsertIntf()
            self.delete.DATA_WIDTH = 0

        self.clean = HandshakeSync()

    def _declr(self):
        self._declr_outer_io()
        self.tables = HObjList(
            HashTableIntf()._m()
            for _ in range(self.TABLE_CNT))
        self.configure_tables(self.tables)

    def configure_tables(self, tables: List[HashTableCore]):
        """
        share the configuration with the table engines
        """
        for t in tables:
            t._updateParamsFrom(self)
            t.ITEMS_CNT = self.TABLE_SIZE // self.TABLE_CNT
            t.LOOKUP_HASH = True
            t.LOOKUP_KEY = True

    def clean_addr_iterator(self, en):
        lastAddr = self.TABLE_SIZE // self.TABLE_CNT - 1
        addr = self._reg("cleanupAddr",
                         Bits(log2ceil(lastAddr), signed=False),
                         def_val=0)
        last = addr._eq(lastAddr)
        If(en,
            If(last,
                addr(0)
            ).Else(
                addr(addr + 1)
           )
        )

        return addr, last

    def tables_insert_driver(self, state: RtlSignal, insertTargetOH: RtlSignal,
                             insertIndex: RtlSignal, stash: RtlSignal):
        """
        :param state: state register of main FSM
        :param insertTargetOH: index of table where insert should be performed,
            one hot encoding
        :param insertIndex: address for table where item should be placed
        :param stash: stash register with data for insert/lookup/delete from table
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

    def tables_lookupRes_resolver(self, insertResRead: RtlSignal):
        """
        Control lookupRes interface for each table
        """
        tables = self.tables
        # one hot encoded index where item should be stored (where was found
        # or where is place)
        insertTargetOH = self._reg("insertTargetOH", Bits(self.TABLE_CNT, force_vector=True))

        res = [t.lookupRes for t in tables]
        insertFinal = self._reg("insertFinal")
        # select empty space or victim which which current insert item
        # should be swapped with
        lookupResVld = StreamNode(masters=res).ack()
        lookupFoundOH = [t.lookupRes.found for t in tables]
        isEmptyOH = [~t.lookupRes.occupied for t in tables]

        If(insertResRead & lookupResVld,
            # resolve in which table the item should be stored
            If(Or(*lookupFoundOH),
                # an item found in some table, set target to this table
                insertTargetOH(Concat(*reversed(lookupFoundOH)))
            ).Else(
                # set target to first table with an empty item
                SwitchLogic(
                    [(isEmpty, insertTargetOH(1 << i))
                     for i, isEmpty in enumerate(isEmptyOH)],
                    # if there is no empty place in any table, swap
                    # item with an item from next table or last table
                    # if this is a first insert
                    default=If(insertTargetOH != 0,
                                insertTargetOH(ror(insertTargetOH, 1))
                            ).Else(
                                insertTargetOH(1 << (self.TABLE_CNT - 1))
                            )
                )
            ),
            # final if the item was already somewhere or there is an empty place in some table
            insertFinal(Or(*lookupFoundOH, *isEmptyOH))
        )
        return lookupResVld, insertFinal, lookupFoundOH, insertTargetOH

    def insert_addr_select(self, insertTargetOH, state, cleanAddr):
        """
        Select a insert address
        """
        insertIndex = self._sig("insertIndex", Bits(self.HASH_WIDTH))
        If(state._eq(state._dtype.cleaning),
            insertIndex(cleanAddr)
        ).Else(
            SwitchLogic([(insertTargetOH[i],
                          insertIndex(t.lookupRes.hash))
                         for i, t in enumerate(self.tables)],
                        default=insertIndex(None))
        )
        return insertIndex

    def stash_load(self, isIdle, lookupResNext, insertTargetOH, stash, lookup_not_in_progress, another_lookup_possible):
        """
        load a stash register from lookup/insert/delete interface
        """
        lookup = self.lookup
        insert = self.insert
        delete = self.delete
        table_lookup_ack = StreamNode(slaves=[t.lookup for t in self.tables]).ack()
        lookup_currently_executed = stash.origin_op._eq(ORIGIN_TYPE.LOOKUP)
        assert self.MAX_REINSERT > 0, self.MAX_REINSERT
        If(isIdle,
            If(lookup_not_in_progress & self.clean.vld,
                stash.origin_op(ORIGIN_TYPE.DELETE),
                stash.item_vld(0)
            ).Elif(lookup_not_in_progress & delete.vld,
                stash.origin_op(ORIGIN_TYPE.DELETE),
                stash.key(delete.key),
                stash.item_vld(0),
            ).Elif(lookup_not_in_progress & insert.vld,
                stash.origin_op(ORIGIN_TYPE.INSERT),
                stash.key(insert.key),
                stash.data(insert.data),
                stash.reinsert_cntr(self.MAX_REINSERT),
                stash.item_vld(1),
            ).Elif(lookup.vld & lookup.rd,
                stash.origin_op(ORIGIN_TYPE.LOOKUP),
                stash.key(lookup.key),
            ).Elif(table_lookup_ack,
                stash.origin_op(ORIGIN_TYPE.DELETE),  # need to set something else than lookup
                stash.key(None),
            )
        ).Elif(lookupResNext,
            SwitchLogic([
                (insertTargetOH[i],
                    [
                        # load stash from item found previously
                        # :note: happens in same time as write to table
                        #     so the stash and item in table is swapped
                        stash.key(t.lookupRes.key),
                        stash.data(t.lookupRes.data),
                        stash.reinsert_cntr(stash.reinsert_cntr - 1),
                        stash.item_vld(t.lookupRes.occupied),
                    ]
                  )
                  for i, t in enumerate(self.tables)
                ],
                default=[
                    stash.origin_op(ORIGIN_TYPE.DELETE),
                    stash.key(None),
                    stash.data(None),
                    stash.reinsert_cntr(None),
                    stash.item_vld(None),
                ])
        )
        cmd_priority = [self.clean, self.delete, self.insert, lookup]
        for i, intf in enumerate(cmd_priority):
            withLowerPrio = cmd_priority[:i]
            rd = And(isIdle, *[~x.vld for x in withLowerPrio])
            if intf is lookup:
                rd = rd & (~lookup_currently_executed |  # the stash not loaded yet
                     table_lookup_ack  # stash will be consumed
                    ) & another_lookup_possible
            else:
                rd = rd & lookup_not_in_progress

            intf.rd(rd)

    def tables_lookup_driver(self, state: RtlSignal, tableKey: RtlSignal, lookup_en: RtlSignal):
        """
        Connect a lookup ports of all tables
        """
        for t in self.tables:
            t.lookup.key(tableKey)

        # activate lookup only in lookup state (for insert/delete) or if idle and processing lookups
        StreamNode(slaves=[t.lookup for t in self.tables]).sync(lookup_en)

    def lookupRes_driver(self, state: RtlSignal, lookupFoundOH: RtlSignal):
        """
        If lookup request comes from external interface "lookup" propagate results
        from tables to "lookupRes".
        """
        fsm_t = state._dtype
        lookupRes = self.lookupRes
        lookupResVld = StreamNode(masters=[t.lookupRes for t in self.tables]).ack()
        lookupRes.vld(state._eq(fsm_t.idle) & lookupResVld)

        SwitchLogic([(lookupFoundOH[i],
                      lookupRes(t.lookupRes,
                                exclude={lookupRes.vld,
                                         lookupRes.rd}))
                     for i, t in enumerate(self.tables)],
                    default=[
                        lookupRes(self.tables[0].lookupRes,
                                  exclude={lookupRes.vld,
                                           lookupRes.rd})]
                    )

    def lookup_trans_cntr(self):
        """
        create a counter of pure lookup operations in progress
        """
        lookup = self.lookup
        lookupRes = self.lookupRes
        lookup_in_progress = self._reg("lookup_in_progress", Bits(log2ceil(self.MAX_LOOKUP_OVERLAP - 1)), def_val=0)
        lookup_trans = lookup.rd & lookup.vld
        lookupRes_trans = lookupRes.rd & lookupRes.vld

        If(lookup_trans & ~lookupRes_trans,
            lookup_in_progress(lookup_in_progress + 1)
        ).Elif(~lookup_trans & lookupRes_trans,
            lookup_in_progress(lookup_in_progress - 1)
        )
        return lookup_in_progress

    def insertRes_driver(self, state, stash, insertAck, insertFinal, isDelete):
        fsm_t = state._dtype
        res = self.insertRes
        res.vld(
            (state._eq(fsm_t.lookup) & stash.origin_op._eq(ORIGIN_TYPE.INSERT) & stash.reinsert_cntr._eq(0)) |
            (state._eq(fsm_t.lookupResAck) & insertAck & insertFinal & ~isDelete)
        )
        #If(state._eq(fsm_t.lookup),
        res.key(stash.key)
        res.data(stash.data)
        res.pop(stash.reinsert_cntr._eq(0))
        #).Else(
        #   res.key(None),
        #   res.data(None),
        #   res.pop(None),
        #)

    def _impl(self):
        propagateClkRstn(self)

        # stash is storage for item which is going to be swapped with actual
        stash_t = HStruct(
            (Bits(self.KEY_WIDTH), "key"),
            (Bits(self.DATA_WIDTH), "data"),
            (Bits(log2ceil(self.MAX_REINSERT + 1)), "reinsert_cntr"),
            (BIT, "item_vld"),
            (ORIGIN_TYPE, "origin_op"),
        )
        stash = self._reg("stash", stash_t, def_val={"origin_op": ORIGIN_TYPE.DELETE})

        cleanAck = self._sig("cleanAck")
        cleanAddr, cleanLast = self.clean_addr_iterator(cleanAck)
        lookupResRead = self._sig("lookupResRead")
        (lookupResVld,
         insertFinal,
         lookupFoundOH,
         insertTargetOH) = self.tables_lookupRes_resolver(lookupResRead)
        lookupAck = StreamNode(slaves=[t.lookup for t in self.tables]).ack()
        insertAck = StreamNode(slaves=[t.insert for t in self.tables]).ack()

        lookup_in_progress = self.lookup_trans_cntr()
        lookup_not_in_progress = rename_signal(self,
            lookup_in_progress._eq(0) & (stash.origin_op != ORIGIN_TYPE.LOOKUP),
            "lookup_not_in_progress")
        isDelete = stash.origin_op._eq(ORIGIN_TYPE.DELETE)
        isInsert = stash.origin_op._eq(ORIGIN_TYPE.INSERT)
        # lookup is not blocking and does not use FSM bellow
        # this FSM handles only lookup for insert/delete
        fsm_t = HEnum("insertFsm_t", ["idle", "cleaning",
                                      "lookup", "lookupResWaitRd",
                                      "lookupResAck"])
        state = FsmBuilder(self, fsm_t, "insertFsm")\
            .Trans(fsm_t.idle,
                   # wait before lookup_in_progress reaches 0
                   # (new transactions should not be allowed if command has vld)
                   (lookup_not_in_progress & self.clean.vld, fsm_t.cleaning),
                   # before each insert suitable place has to be searched first
                   (lookup_not_in_progress & (self.insert.vld | self.delete.vld), fsm_t.lookup)
            ).Trans(fsm_t.cleaning,
                # walk all items and clean it's item_vlds
                (insertAck & cleanLast, fsm_t.idle),
            ).Trans(fsm_t.lookup,
                # insert timeout
                (stash.reinsert_cntr._eq(0) & isInsert & self.insertRes.rd, fsm_t.idle),
                # search and resolve in which table item
                # should be stored
                (((stash.reinsert_cntr != 0) | ~isInsert) & lookupAck, fsm_t.lookupResWaitRd)
            ).Trans(fsm_t.lookupResWaitRd,
                # process result of lookup and
                (lookupResVld, fsm_t.lookupResAck)
            ).Trans(fsm_t.lookupResAck,
                # process lookupRes, if we are going to insert on place where
                # valid item is, this item has to be stored to stash
                (isDelete, fsm_t.idle),
                # insert into specified table
                (insertAck & insertFinal & (isDelete | self.insertRes.rd), fsm_t.idle),
                # insert and swap with some valid item from the table
                # which we need to store somewhere as well
                (insertAck & ~insertFinal, fsm_t.lookup)
            ).stateReg

        cleanAck(insertAck & state._eq(fsm_t.cleaning))
        lookupResRead(state._eq(fsm_t.lookupResWaitRd))
        lookupResNext = rename_signal(
            self,
            (state._eq(fsm_t.idle) & self.lookupRes.rd) |
            (state._eq(fsm_t.lookupResAck) & (state.next != fsm_t.lookupResAck)),
            "lookupResNext")
        # synchronize all lookupRes from all tables
        StreamNode(masters=[t.lookupRes for t in self.tables]).sync(lookupResNext)

        self.stash_load(
            state._eq(fsm_t.idle),
            lookupResNext,
            insertTargetOH,
            stash,
            lookup_not_in_progress,
            lookup_in_progress != self.MAX_LOOKUP_OVERLAP - 1)
        insertIndex = self.insert_addr_select(insertTargetOH, state, cleanAddr)
        self.insertRes_driver(state, stash, insertAck, insertFinal, isDelete)
        self.tables_insert_driver(state, insertTargetOH, insertIndex, stash)
        self.lookupRes_driver(state, lookupFoundOH)

        lookup_en =rename_signal(
            self,
            (state._eq(fsm_t.lookup) & ((stash.reinsert_cntr != 0) | isDelete)) |
            (state._eq(fsm_t.idle) & stash.origin_op._eq(ORIGIN_TYPE.LOOKUP)),
            "lookup_en"
        )
        self.tables_lookup_driver(state, stash.key, lookup_en)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = CuckooHashTable()
    u.TABLE_CNT = 2
    print(to_rtl_str(u))
