#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, Concat, If
from hwt.code_utils import rename_signal
from hwt.constants import READ, WRITE
from hwt.hObjList import HObjList
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.hwIOStruct import HwIOStruct, HdlType_to_HwIO
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal, \
    HwIOBramPort_noClk, HwIODataVld, HwIORdVldSync
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi_common import Axi_id
from hwtLib.amba.axi_comp.cache.addrTypeConfig import CacheAddrTypeConfig
from hwtLib.commonHwIO.addr import HwIOAddrRdVld
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwtLib.mem.ram import RamSingleClock


class HwIOAxiCacheTagArrayLookupRes(HwIORdVldSync):
    """
    Interface used for r/w logic of cache to return result of search in cache

    :ivar way: the index of way where the tag was found (valid only if found=1)

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ID_WIDTH = HwParam(4)
        HwIOAxiCacheTagArrayUpdate.hwConfig(self)
        self.TAG_T = HwParam(None)

    @override
    def hwDeclr(self):
        Axi_id.hwDeclr(self)
        self.found = HwIOSignal()
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        if self.WAY_CNT > 1:
            self.way = HwIOVectSignal(log2ceil(self.WAY_CNT - 1))
        if self.TAG_T is not None:
            self.tags = HObjList(HdlType_to_HwIO().apply(self.TAG_T) for _ in range(self.WAY_CNT))

        HwIORdVldSync.hwDeclr(self)


class HwIOAxiCacheTagArrayUpdate(HwIODataVld):
    """
    Interface used to insert or delete records in tag array.

    :ivar addr: address to store in tag array
    :note: address is split on index, tag, offset and then stored
    :ivar delete: If true the record will be deleted form array
        else new record will be inserted.

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.WAY_CNT = HwParam(4)
        self.ADDR_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        if self.WAY_CNT > 1:
            self.way_en = HwIOVectSignal(self.WAY_CNT)
        self.delete = HwIOSignal()
        self.vld = HwIOSignal()


class AxiCacheTagArray(CacheAddrTypeConfig):
    """
    Storage of cache tags, cache line state bits (valid/shared/dirty...), pseudo-LRU bits

    .. figure:: ./_static/AxiCacheTagArray.png

    :attention: memories of this component are not cleaned on restart and they need to be initialized using
        specified interfaces externally
    :ivar CACHE_LINE_CNT: a total number of cachelines in this array
    :ivar UPDATE_PORT_CNT: number of ports used for record update
    :ivar CACHE_LINE_SIZE: size of cacheline [B]

    :see: :meth:`~.AxiCacheTagArrayLookupIntf._config`
    :see: :meth:`~.HwIOAxiCacheTagArrayLookupRes._config`

    .. hwt-autodoc:: _example_AxiCacheTagArray
    """

    @override
    def hwConfig(self):
        self.PORT_CNT = HwParam(2)
        self.UPDATE_PORT_CNT = HwParam(1)
        self.ID_WIDTH = HwParam(4)
        HwIOAxiCacheTagArrayUpdate.hwConfig(self)
        CacheAddrTypeConfig.hwConfig(self)
        self.LOOKUP_LATENCY = 1
        self.MAX_BLOCK_DATA_WIDTH = HwParam(None)

    def define_tag_record_t(self):
        tag_record_t = [
            # tag specifies which cacheline is currently loaded
            (HBits(self.TAG_W), "tag"),
            # valid specifies if record on this row is valid or not
            # valid can be altered on cacheline flush or fill
            (BIT, "valid"),
        ]
        # :note: it is important that the record is aligned to byte boundary
        # because we will use byte-enable on ram port to update this item in array of such a items
        misalign = (self.TAG_W + 1) % 8
        if misalign != 0:
            tag_record_t.append((HBits(8 - misalign), None))
        return HStruct(*tag_record_t)

    @override
    def hwDeclr(self):
        self._compupte_tag_index_offset_widths()
        self.tag_record_t = self.define_tag_record_t()
        addClkRstn(self)
        with self._hwParamsShared():
            self.lookup = HObjList(
                HwIOAddrRdVld()
                for _ in range(self.PORT_CNT)
            )
            self.lookupRes = HObjList(
                HwIOAxiCacheTagArrayLookupRes()._m()
                for _ in range(self.PORT_CNT)
            )
            for i in self.lookupRes:
                i.TAG_T = self.tag_record_t
            self.update = HObjList(
                HwIOAxiCacheTagArrayUpdate()
                for _ in range(self.UPDATE_PORT_CNT)
            )

        tag_mem = self.tag_mem = RamSingleClock()
        tag_mem.ADDR_WIDTH = log2ceil(self.CACHE_LINE_CNT // self.WAY_CNT - 1)
        tag_mem.DATA_WIDTH = self.tag_record_t.bit_length() * self.WAY_CNT
        tag_mem.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        tag_mem.PORT_CNT = (
            *(WRITE for _ in range(self.UPDATE_PORT_CNT)),
            *(READ for _ in range(self.PORT_CNT)),
        )
        tag_mem.HAS_BE = True

    def connect_update_port(self, update: HwIOAxiCacheTagArrayUpdate, tag_mem_port_w: HwIOBramPort_noClk):
        update_tmp = self._reg(
            "update_tmp",
            HStruct(
                (update.addr._dtype, "addr"),
                (BIT, "delete"),
                (update.way_en._dtype, "way_en"),
                (BIT, "vld"),
            ),
            def_val={"vld": 0}
        )
        update_tmp(update)
        tag, index, _ = self.parse_addr(update.addr)

        tag_mem_port_w.en(update.vld)
        tag_mem_port_w.addr(index)

        # construct the byte enable mask for various tag enable configurations
        # prepare write tag in every way but byte enable only requested ways
        tag_record = self.tag_record_t.from_py({
            "tag": tag,
            "valid":~update.delete,
        })
        tag_record = tag_record._reinterpret_cast(HBits(self.tag_record_t.bit_length()))
        tag_mem_port_w.din(Concat(*(tag_record for _ in range(self.WAY_CNT))))
        tag_be_t = HBits(self.tag_record_t.bit_length() // 8)
        tag_en = tag_be_t.from_py(tag_be_t.all_mask())
        tag_not_en = tag_be_t.from_py(0)
        tag_mem_port_w.we(Concat(*reversed([
            en._ternary(tag_en, tag_not_en)
            for en in update.way_en
        ])))
        return update_tmp

    def connect_lookup_port(self,
                lookup: HwIOAddrRdVld,
                tag_mem_port_r: HwIOBramPort_noClk,
                lookupRes: HwIOAxiCacheTagArrayLookupRes,
                update_tmp: HwIOStruct):
        lookup_tmp = self._reg(
            "lookup_tmp",
            HStruct(
                *([(lookup.id._dtype, "id")] if lookup.ID_WIDTH else ()),
                (lookup.addr._dtype, "addr"),
                (BIT, "vld")
            ),
            def_val={"vld": 0}
        )

        pa = self.parse_addr
        just_updated = rename_signal(
            self,
            # updated on same index (using "update" port) = the result which is currently on output
            # of the ram may be invalid
            update_tmp.vld & pa(lookup_tmp.addr)[1]._eq(pa(update_tmp.addr)[1]),
            "just_updated"
        )

        # tag comparator
        tag, _, _ = self.parse_addr(lookup_tmp.addr)
        tags = tag_mem_port_r.dout._reinterpret_cast(self.tag_record_t[self.WAY_CNT])
        found = [
            # is matching and just this tag was not updated
            (
                t.valid &
                t.tag._eq(tag) &
                (~just_updated | (update_tmp.vld & ~update_tmp.way_en[i]))
            ) | (
                # or was updated to the matching tag
                just_updated &
                update_tmp.way_en[i] &
                ~update_tmp.delete &
                pa(lookup_tmp.addr)[0]._eq(pa(update_tmp.addr)[0])
            )
            for i, t in enumerate(tags)
        ]

        # if the data which is currently on output of the ram was
        # just updated it means that the data is invalid and the update
        # data will be lost in next clock cycle, if the consumer of lookupRes
        # can not consume the data just know, we need to perform lookup in tag_array
        # once again
        lookup.rd(~lookup_tmp.vld | lookupRes.rd)
        If(lookup.rd,
            lookup_tmp.id(lookup.id) if lookup.ID_WIDTH else [],
            lookup_tmp.addr(lookup.addr),
        )
        lookup_tmp.vld(lookup.vld | (lookup_tmp.vld & ~lookupRes.rd))

        tag_mem_port_r.addr((lookup_tmp.vld & ~lookupRes.rd)._ternary(
            self.parse_addr(lookup_tmp.addr)[1],  # lookup previous address and look for a change
            self.parse_addr(lookup.addr)[1],  # lookup a new address
        ))
        tag_mem_port_r.en(lookup.vld | (lookup_tmp.vld & ~lookupRes.rd))

        if lookupRes.ID_WIDTH:
            lookupRes.id(lookup_tmp.id)
        lookupRes.addr(lookup_tmp.addr)
        lookupRes.way(oneHotToBin(self, found))
        lookupRes.found(Or(*found))
        lookupRes.tags(tags)

        lookupRes.vld(lookup_tmp.vld)

    @override
    def hwImpl(self):
        if self.UPDATE_PORT_CNT == 1:
            update_tmp = self.connect_update_port(
                self.update[0],
                self.tag_mem.port[0]
            )
            for lookup, tag_mem_port, lookupRes in zip(self.lookup,
                                                       self.tag_mem.port[1:],
                                                       self.lookupRes):
                self.connect_lookup_port(
                    lookup,
                    tag_mem_port,
                    lookupRes,
                    update_tmp
                )
        else:
            raise NotImplementedError()

        propagateClkRstn(self)


def _example_AxiCacheTagArray():
    m = AxiCacheTagArray()
    m.PORT_CNT = 2
    m.UPDATE_PORT_CNT = 1
    m.MAX_BLOCK_DATA_WIDTH = 8
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_AxiCacheTagArray()
    print(to_rtl_str(m))
