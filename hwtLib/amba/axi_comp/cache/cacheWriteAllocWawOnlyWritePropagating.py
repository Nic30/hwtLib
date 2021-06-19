#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import Or, SwitchLogic
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.hsStructIntf import HsStructIntf
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil, isPow2
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axi4 import Axi4, Axi4_r, Axi4_addr, Axi4_w, Axi4_b
from hwtLib.amba.axi_comp.cache.addrTypeConfig import CacheAddrTypeConfig
from hwtLib.amba.axi_comp.cache.lru_array import AxiCacheLruArray, IndexWayHs
from hwtLib.amba.axi_comp.cache.tag_array import AxiCacheTagArray, \
    AxiCacheTagArrayLookupResIntf, AxiCacheTagArrayUpdateIntf
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.constants import RESP_OKAY, BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, BYTES_IN_TRANS, PROT_DEFAULT, QOS_DEFAULT
from hwtLib.common_nonstd_interfaces.addr_hs import AddrHs
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.binToOneHot import binToOneHot
from hwtLib.mem.ramTransactional import RamTransactional
from hwtLib.mem.ramTransactional_io import TransRamHsR, TransRamHsW
from pyMathBitPrecise.bit_utils import mask


# https://chipress.co/category/job-roles-titles/page/16/
# https://chipress.co/2019/04/13/can-you-show-the-state-transition-for-snoop-based-scheme-using-msi-protocol/
# https://github.com/airin711/Verilog-caches
# https://github.com/rajshadow/4-way-set-associative-cache-verilog
# https://github.com/xdesigns/4way-cache
# https://github.com/prasadp4009/2-way-Set-Associative-Cache-Controller
class AxiCacheWriteAllocWawOnlyWritePropagating(CacheAddrTypeConfig):
    """
    Non-blocking pipelined Set Associative cache for AXI interfaces which is designed
    to work with an LSU which solves only WAW (write-after-write) conflicts.


    :note: Write propagation in this context means that any read received will contain lastly written
        data in some time few clock before (derived from read latency of the LSU)
        the actual request (due to latency of the read resolution).
        This means that if master check last N transaction for collision the data is asserted to be
        in last version or to be marked with an invalidation flag. The N is usually 3 and
        is derived from the latency of LSU which should be connected behind this cache.

    :attention: This cache solves only WAW conflicts, this means that WAR and RAW conflicts
        are left unsolved and must be handled on master side. This is suitable for a cumulative
        operations in general as together with write propagating it allows master component
        to significantly reduce buffers and collision detection logic.

    .. figure:: ./_static/AxiCacheWriteAllocWawOnlyWritePropagating.png

    :see: :class:`hwtLib.amba.axi_comp.cache.CacheAddrTypeConfig`
    :ivar DATA_WIDTH: data width of interfaces
    :ivar WAY_CNT: number of places where one cache line can be stored

    :note: 1-way associative = directly mapped
    :note: This cache does not check access collision with a requests to main (slave) memory.
        It only provides an information for LSU to do so. The LSU is supposed to be connected
        between main memory and this cache (= on master port where slave should be connected).

    * The tag_array contains tags and cache line status flags for cache lines.
    * The lsu_array contains the data for data for pseudo LRU (Last Recently Used) cache replacement policy.
      It is stored in a separate array due to high requirements for concurrent access which results
      in increased memory consumption.
    * The data_array is a RAM where data for cache lines is stored.

    The memories are separated because they have a different memory port requirements
    and we want to keep the number of memory ports and the size of the memory minimal
    as resource requirements grow exponentially with increasing number of memory ports.

    .. hwt-autodoc:: _example_AxiCacheWriteAllocWawOnlyWritePropagating
    """

    def _config(self):
        Axi4._config(self)
        self.WAY_CNT = Param(4)
        self.MAX_BLOCK_DATA_WIDTH = Param(None)
        CacheAddrTypeConfig._config(self)

    def _declr(self):
        assert self.CACHE_LINE_CNT > 0, self.CACHE_LINE_CNT
        assert self.WAY_CNT > 0 and isPow2(self.WAY_CNT), self.WAY_CNT
        assert self.CACHE_LINE_CNT % self.WAY_CNT == 0, (self.CACHE_LINE_CNT, self.WAY_CNT)
        assert isPow2(self.CACHE_LINE_SIZE // (self.DATA_WIDTH // 8))
        assert self.DATA_WIDTH % 8 == 0, self.DATA_WIDTH
        self._compupte_tag_index_offset_widths()

        addClkRstn(self)
        with self._paramsShared():
            self.s = Axi4()
            self.m = Axi4()._m()

            rc = self.read_cancel = AddrHs()._m()
            rc.ID_WIDTH = 0

            self.tag_array = AxiCacheTagArray()
            self.lru_array = AxiCacheLruArray()
            for a in [self.tag_array, self.lru_array]:
                a.PORT_CNT = 2  # r+w

        da = RamTransactional()
        da.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        da.WORD_WIDTH = self.CACHE_LINE_SIZE * 8
        da.DATA_WIDTH = self.DATA_WIDTH
        da.ADDR_WIDTH = log2ceil(self.CACHE_LINE_CNT)
        da.R_ID_WIDTH = self.ID_WIDTH
        da.W_PRIV_T = HStruct(
            # used to construct an address for flush of original item in cache which is beeing replaced
            (Bits(self.TAG_W), "victim_tag"),  # index part of address is an address on flush_data.addr channel
            (Bits(self.ID_WIDTH), "id"),
        )
        self.data_array = da

        # self.flush = HandshakeSync()
        # self.init = HandshakeSync()

    def axiAddrDefaults(self, a: Axi4_addr):
        a.burst(BURST_INCR)
        a.len(self.CACHE_LINE_SIZE // (self.DATA_WIDTH // 8) - 1)
        a.cache(CACHE_DEFAULT)
        a.lock(LOCK_DEFAULT)
        a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
        a.prot(PROT_DEFAULT)
        a.qos(QOS_DEFAULT)

    def connect_tag_lookup(self):
        in_ar, in_aw = self.s.ar, self.s.aw
        # connect address lookups to a tag array
        tags = self.tag_array
        for a, tag_lookup in zip((in_ar, in_aw), tags.lookup):
            tag_lookup.addr(a.addr)
            tag_lookup.id(a.id)
            if a is in_aw:
                rc = self.read_cancel
                rc.addr(a.addr)
                StreamNode([a], [tag_lookup, rc]).sync()
            else:
                StreamNode([a], [tag_lookup]).sync()

    def incr_lru_on_hit(self,
                        lru_incr: IndexWayHs,
                        tag_res: AxiCacheTagArrayLookupResIntf):
        index = self.parse_addr(tag_res.addr)[1]
        lru_incr.vld(tag_res.vld & tag_res.found)
        lru_incr.way(tag_res.way)
        lru_incr.index(index)

    def read_handler(self,
                     ar_tagRes: AxiCacheTagArrayLookupResIntf,  # in
                     axi_s_r: Axi4_r,  # out
                     ar_lru_incr: IndexWayHs,  # out
                     da_r: TransRamHsR,  # in
                     axi_m_ar: Axi4_addr,  # out
                     axi_m_r: Axi4_r  # in
                     ):
        """
        :param ar_tagRes: Read request including information from tag_array for given tag.
        :param axi_s_r: Read data requested by ar_tagRes.
        :param ar_lru_incr: Incrementing LRU for given address when tag is found.
        :param da_r: Read interface of data_array used when tag is found.
        :param axi_m_ar: Read address request interface to memory when tag is not found.
        :param axi_m_r: Read data requested by axi_m_ar from memory when tag is not found.

        .. figure:: ./_static/AxiCacheWriteAllocWawOnlyWritePropagating_read_handler.png
        """
        self.incr_lru_on_hit(ar_lru_incr, ar_tagRes)

        # addd a register with backup register for poential overflow
        # we need this as we need to check if we can store data in advance.
        # this is because we need a higher priority for flushing
        # in order to avoid deadlock.
        data_arr_read_req = HsBuilder(self, da_r.addr, master_to_slave=False)\
            .buff(1, latency=(1, 2))\
            .end

        # send read request to data_array
        ar_index = self.parse_addr(ar_tagRes.addr)[1]
        data_arr_read_req.priv(ar_tagRes.id)
        data_arr_read_req.addr(self.addr_in_data_array(ar_tagRes.way, ar_index)),

        # delegate read request to m.ar if not hit
        StreamNode(
            [ar_tagRes],
            [axi_m_ar, data_arr_read_req],
            extraConds={
                axi_m_ar: ar_tagRes.vld & ~ar_tagRes.found,
                data_arr_read_req: ar_tagRes.vld & ar_tagRes.found,
            },
            skipWhen={
                axi_m_ar: ar_tagRes.vld & ar_tagRes.found,
                data_arr_read_req: ar_tagRes.vld & ~ar_tagRes.found,
            },
        ).sync()

        axi_m_ar.addr(ar_tagRes.addr)
        axi_m_ar.id(ar_tagRes.id)
        self.axiAddrDefaults(axi_m_ar)

        data_arr_read = axi_s_r.__class__()
        data_arr_read._updateParamsFrom(axi_s_r)
        self.data_arr_read = data_arr_read

        data_arr_read(da_r.data, exclude=[data_arr_read.resp])
        data_arr_read.resp(RESP_OKAY)

        data_arr_read = AxiSBuilder(self, data_arr_read)\
            .buff(1, latency=(1, 2))\
            .end

        s_r = AxiSBuilder.join_prioritized(self, [
            data_arr_read,
            axi_m_r,
        ]).end
        axi_s_r(s_r)

    def resolve_victim(self, st0_o_tag_found: RtlSignal,  # in
                       st0_o_found_way: RtlSignal,  # in
                       st0_o_tags: List[StructIntf],  # in
                       victim_way: Handshaked  # in
                       ):
        _victim_way = self._sig("victim_way_tmp", Bits(log2ceil(self.WAY_CNT)))
        _victim_tag = self._sig("victim_tag_tmp", Bits(self.TAG_W))
        SwitchLogic(
            [
                # select first empty tag
                (~tag.valid, [
                    _victim_way(i),
                    _victim_tag(tag.tag),
                ]) for i, tag in enumerate(st0_o_tags)
            ],
            default=[
                # select an victim specified by victim_way
                _victim_way(victim_way.data),
                SwitchLogic([
                        (victim_way.data._eq(i), _victim_tag(tag.tag))
                        for i, tag in enumerate(st0_o_tags)
                    ],
                    default=_victim_tag(None)
                )
            ]
        )
        _victim_way = st0_o_tag_found._ternary(st0_o_found_way, _victim_way)
        return _victim_way, _victim_tag

    def write_handler(self,
                      aw_tagRes: AxiCacheTagArrayLookupResIntf,  # in
                      axi_s_b: Axi4_b,  # out
                      aw_lru_incr: IndexWayHs,  # out
                      victim_way_req: AddrHs, victim_way_resp: Handshaked,  # out, in
                      da_w: TransRamHsW,  # in
                      tag_update: AxiCacheTagArrayUpdateIntf,  # out
                      ):
        """
        :param aw_tagRes: Write request including in information from tag_array for given tag.
        :param axi_s_b: Response requested by aw_tagRes
        :param aw_lru_incr: Incrementing LRU for given address when tag is found.
        :param victim_way_req: Request victim from LRU array for a specified index, when cache is full.
        :param victim_way_resp: Victim address requested by victim_way_req
        :param da_w: Write interface of data_array to write and initiate flush when cache is full.
        :param tag_update: Tag update interface for newly written data.

        .. figure:: ./_static/AxiCacheWriteAllocWawOnlyWritePropagating_write_handler.png
        """
        # note that the lru update happens even if the data is stalled
        # but that is not a problem because it wont change the order of the usage
        # of the cahceline
        self.incr_lru_on_hit(aw_lru_incr, aw_tagRes)

        st0 = HandshakedReg(HsStructIntf)
        st0.T = HStruct(
            # the original id and address of a write transaction
            (self.s.aw.id._dtype, "write_id"),
            (self.s.aw.addr._dtype, "replacement_addr"),
            # array of tags for cachelines with this index
            (aw_tagRes.TAG_T[aw_tagRes.WAY_CNT], "tags"),
            (BIT, "tag_found"),
            (BIT, "had_empty"),  # had some empty tag
            (aw_tagRes.way._dtype, "found_way"),  # way of where tag was found
        )
        self.victim_load_status0 = st0

        st0_i = st0.dataIn.data
        # resolve if we need to select a victim and optianally ask for it
        has_empty = rename_signal(self, Or(*(~t.valid for t in aw_tagRes.tags)), "has_empty")
        st0_i.write_id(aw_tagRes.id),
        st0_i.replacement_addr(aw_tagRes.addr),
        st0_i.tags(aw_tagRes.tags),
        st0_i.tag_found(aw_tagRes.found),
        st0_i.found_way(aw_tagRes.way),
        st0_i.had_empty(has_empty),

        victim_way_req.addr(self.parse_addr(aw_tagRes.addr)[1])
        StreamNode(
            [aw_tagRes],
            [victim_way_req, st0.dataIn],
            skipWhen={
                victim_way_req: aw_tagRes.vld & (
                                aw_tagRes.found |
                                has_empty
                            )
            },
            extraConds={
                victim_way_req:~aw_tagRes.found & ~has_empty
            }
        ).sync()

        ########################## st1 - pre (read request resolution, victim address resolution) ##############

        st0_o = st0.dataOut.data

        _victim_way, _victim_tag = self.resolve_victim(st0_o.tag_found, st0_o.found_way, st0_o.tags, victim_way_resp)

        da_w.addr.flush(rename_signal(self, st0.dataOut.vld & (~st0_o.had_empty & ~st0_o.tag_found), "need_to_flush"))
        da_w.addr.priv.id(st0_o.write_id)
        da_w.addr.addr(self.addr_in_data_array(st0_o.tag_found._ternary(st0_o.found_way, _victim_way),
                                               self.parse_addr(st0_o.replacement_addr)[1])),
        da_w.addr.priv.victim_tag(_victim_tag)

        MULTI_WORD = self.data_array.ITEM_WORDS > 1
        if MULTI_WORD:
            st1_id = HandshakedReg(Handshaked)
            st1_id.LATENCY = (1, 2)
            st1_id.DATA_WIDTH = self.ID_WIDTH
            self.victim_load_status1 = st1_id
            st1_id.dataIn.data(st0_o.write_id)
        # placed between st0, st1
        StreamNode(
            [victim_way_resp, st0.dataOut],
            [da_w.addr, st1_id.dataIn] if MULTI_WORD else [da_w.addr],
            extraConds={
                victim_way_resp:~st0_o.tag_found & ~st0_o.had_empty,
            },
            skipWhen={
                victim_way_resp: st0_o.tag_found | st0_o.had_empty,
            }
        ).sync()

        in_w = AxiSBuilder(self, self.s.w)\
            .buff(self.tag_array.LOOKUP_LATENCY + 4)\
            .end
        if MULTI_WORD:
            StreamNode(
                [in_w, st1_id.dataOut],
                [da_w.data, axi_s_b],
                extraConds={axi_s_b: in_w.last,
                            st1_id.dataOut: in_w.last},
                skipWhen={axi_s_b:~in_w.last,
                          st1_id.dataOut:~in_w.last},
            ).sync()
            axi_s_b.id(st1_id.dataOut.data)  # todo
        else:
            StreamNode(
                [in_w],
                [da_w.data, axi_s_b],
                extraConds={axi_s_b: in_w.last},
                skipWhen={axi_s_b:~in_w.last},
            ).sync()
            axi_s_b.id(st0_o.write_id)
        axi_s_b.resp(RESP_OKAY)

        da_w.data(in_w, exclude=[in_w.ready, in_w.valid])

        tag_update.vld(st0.dataOut.vld & da_w.addr.rd)
        tag_update.delete(0)
        tag_update.way_en(binToOneHot(_victim_way))
        tag_update.addr(st0_o.replacement_addr)
        # [TODO] initial clean
        lru_array_set = self.lru_array.set
        lru_array_set.addr(None)
        lru_array_set.data(None)
        lru_array_set.vld(0)

    def flush_handler(self,
                   flush_data: TransRamHsW,  # in
                   axi_m_aw: Axi4_addr,  # out
                   axi_m_w: Axi4_w,  # out
                   axi_m_b: Axi4_b,  # in
                   ):
        id_tag = flush_data.addr.priv

        # potentially cut msb bits which do specify the way from address
        axi_m_aw.addr(self.deparse_addr(id_tag.victim_tag, flush_data.addr.addr[self.INDEX_W:], 0))
        axi_m_aw.id(id_tag.id)
        self.axiAddrDefaults(axi_m_aw)
        StreamNode(
            [flush_data.addr, ],
            [axi_m_aw, ]
        ).sync()

        axi_m_w.data(flush_data.data.data)
        axi_m_w.strb(mask(axi_m_w.data._dtype.bit_length() // 8))
        axi_m_w.last(flush_data.data.last)

        StreamNode(
            [flush_data.data],
            [axi_m_w],
        ).sync()

        axi_m_b.ready(1)

    def _impl(self):
        """
        Read operation:

        * Use index to lookup in tag memory
        * if tag matches return cacheline else dispatch read request
          (the transaction is dispatched with original id, upon data receive the transaction
          is passed to master without any synchronization with the cache )

        Write operation:

        * Use index to lookup in tag memory
        * If tag matches and the cacheline is not being replaced update the data in data array.
        * If tag is not found in corresponding set select a victim and read it from data array, flush it
          and write back cacheline to array and update tag
        """
        # transaction type usind in data array memory access pipeline

        self.connect_tag_lookup()
        ar_tagRes, aw_tagRes = self.tag_array.lookupRes

        self.read_handler(
            ar_tagRes,
            self.s.r,
            self.lru_array.incr[0],
            self.data_array.r,
            self.m.ar,
            self.m.r,
        )

        self.write_handler(
            aw_tagRes,
            self.s.b,
            self.lru_array.incr[1],
            self.lru_array.victim_req,
            self.lru_array.victim_data,
            self.data_array.w,
            self.tag_array.update[0],
        )
        self.flush_handler(
            self.data_array.flush_data,
            self.m.aw,
            self.m.w,
            self.m.b,
        )

        propagateClkRstn(self)


def _example_AxiCacheWriteAllocWawOnlyWritePropagating():
    u = AxiCacheWriteAllocWawOnlyWritePropagating()
    u.DATA_WIDTH = 16
    u.CACHE_LINE_SIZE = 2
    u.WAY_CNT = 2
    u.CACHE_LINE_CNT = 16
    u.MAX_BLOCK_DATA_WIDTH = 8
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    from hwtLib.xilinx.constants import XILINX_VIVADO_MAX_DATA_WIDTH
    u = AxiCacheWriteAllocWawOnlyWritePropagating()
    u.DATA_WIDTH = 512
    u.CACHE_LINE_SIZE = u.DATA_WIDTH // 8
    u.WAY_CNT = 4
    u.CACHE_LINE_CNT = u.WAY_CNT * 4096
    u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH
    # u.CACHE_LINE_SIZE = 64
    # u.DATA_WIDTH = 512
    # u.WAY_CNT = 2
    # u.CACHE_LINE_CNT = u.WAY_CNT * 4096
    # u = _example_AxiCacheWriteAllocWawOnlyWritePropagating()
    print(to_rtl_str(u))
