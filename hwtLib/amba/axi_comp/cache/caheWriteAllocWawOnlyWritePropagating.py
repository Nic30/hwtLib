#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import If, Or, SwitchLogic, In, connect
from hwt.code_utils import rename_signal
from hwt.hdl.constants import READ, WRITE
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import BramPort_withoutClk, Handshaked, HandshakeSync
from hwt.interfaces.structIntf import StructIntf, HdlType_to_Interface
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axi4 import Axi4, Axi4_r, Axi4_addr
from hwtLib.amba.axi_comp.cache.addrTypeConfig import CacheAddrTypeConfig
from hwtLib.amba.axi_comp.cache.lru_array import AxiCacheLruArray, IndexWayHs
from hwtLib.amba.axi_comp.cache.tag_array import AxiCacheTagArray, \
    AxiCacheTagArrayLookupResIntf, AxiCacheTagArrayUpdateIntf
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.constants import RESP_OKAY, BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, BYTES_IN_TRANS, PROT_DEFAULT, QOS_DEFAULT
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtLib.common_nonstd_interfaces.addr_hs import AddrHs
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.ramAsHs import RamAsHs, RamHsR
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.binToOneHot import binToOneHot
from hwtLib.mem.ram import RamSingleClock
from pyMathBitPrecise.bit_utils import mask


class HsStructIntf(HandshakeSync):

    def _config(self):
        self.T = Param(None)

    def _declr(self):
        assert self.T is not None
        self.data = HdlType_to_Interface().apply(self.T)
        HandshakeSync._declr(self)


class data_trans_t():
    read = 0
    read_and_write = 1
    write = 2
    write_and_flush = 3


# https://chipress.co/category/job-roles-titles/page/16/
# https://chipress.co/2019/04/13/can-you-show-the-state-transition-for-snoop-based-scheme-using-msi-protocol/
# https://github.com/airin711/Verilog-caches
# https://github.com/rajshadow/4-way-set-associative-cache-verilog
# https://github.com/xdesigns/4way-cache
# https://github.com/prasadp4009/2-way-Set-Associative-Cache-Controller
class AxiCaheWriteAllocWawOnlyWritePropagating(CacheAddrTypeConfig):
    """
    Non-blocking pipelined Set Associative cache for AXI interfaces which is designed
    to work with an LSU which solves only WAW (write-after-write) conflicts.


    :note: Write propagation in this context means that any read recieved will contain lastly writen
        data in some time few clock before (derived from read latency of the LSU)
        the actual request (due to latency of the read resolution).
        This means that if master check last N transaction for colisions the data is asserted to be
        in last version or to be marked with an invalidation flag. The N is usually 3 and
        is derived from the latency of LSU which should be connected behind this cache.

    :attention: This cache solves only WAW conflicts, this means that WAR and RAW conflicts
        are left unsolved and must be handled on master side. This is suitable for a cumulative
        operations in general as together with write propagating it allows master component
        to significantly reduce buffers and colision detection logic.

    .. figure:: ./_static/AxiCaheWriteAllocWawOnlyWritePropagating.png

    :see: :class:`hwtLib.amba.axi_comp.cache.CacheAddrTypeConfig`
    :ivar DATA_WIDTH: data width of interfaces
    :ivar WAY_CNT: number of places where one cache line can be stored

    :note: 1-way associative = directly mapped
    :note: This cache does not check access colisions with a requests to main (slave) memory.
        It only provides an information for LSU to do so. The LSU is supposed to be connected
        between main mamory and this cache (= on master port where slave should be connected).

    * The tag_array contains tags and cache line status flags for cache lines.
    * The lsu_array contains the data for data for pseudo LRU (Last Recently Used) cache replacement policy.
      It is stored in a separate array due to high requiremets for concurrent access which results
      in increased memory consumption.
    * The data_array is a RAM where data for cache lines is stored.

    The memories are separated because they have a different memory port requirements
    and we want to keep the number of memory ports and the size of the memory minimal
    as resource requiements grow exponentially with increasing number of memory ports.
    """

    def _config(self):
        Axi4._config(self)
        self.WAY_CNT = Param(4)
        self.MAX_BLOCK_DATA_WIDTH = Param(None)
        CacheAddrTypeConfig._config(self)

    def _declr(self):
        assert self.CACHE_LINE_CNT > 0, self.CACHE_LINE_CNT
        assert self.WAY_CNT > 0, self.WAY_CNT
        assert self.CACHE_LINE_CNT % self.WAY_CNT == 0, (self.CACHE_LINE_CNT, self.WAY_CNT)
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

        # self.flush = HandshakeSync()
        # self.init = HandshakeSync()

        data_array = self.data_array = RamSingleClock()
        data_array.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        data_array.DATA_WIDTH = self.DATA_WIDTH
        data_array.ADDR_WIDTH = log2ceil(
            self.CACHE_LINE_CNT *
            ceil(self.CACHE_LINE_SIZE * 8 / self.DATA_WIDTH)
        )
        data_array.PORT_CNT = (READ, WRITE)
        data_array.HAS_BE = True

    def axiAddrDefaults(self, a: Axi4_addr):
        a.burst(BURST_INCR)
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
                     ar_lru_incr: IndexWayHs,  # out
                     ar_tagRes: AxiCacheTagArrayLookupResIntf,  # in
                     data_arr_read_req: IndexWayHs, data_arr_read: Axi4_r  # out, in
                     ):
        """
        .. figure:: ./_static/AxiCaheWriteAllocWawOnlyWritePropagating_read_handler.png
        """
        self.incr_lru_on_hit(ar_lru_incr, ar_tagRes)

        # send read request to data_array
        ar_index = self.parse_addr(ar_tagRes.addr)[1]
        data_arr_read_req.id(ar_tagRes.id)
        data_arr_read_req.index(ar_index),
        data_arr_read_req.way(ar_tagRes.way)

        # delegate read request to m.ar if not hit
        out_ar = self.m.ar
        StreamNode(
            [ar_tagRes],
            [out_ar, data_arr_read_req],
            extraConds={
                out_ar: ar_tagRes.vld & ~ar_tagRes.found,
                data_arr_read_req: ar_tagRes.vld & ar_tagRes.found,
            },
            skipWhen={
                out_ar: ar_tagRes.vld & ar_tagRes.found,
                data_arr_read_req: ar_tagRes.vld & ~ar_tagRes.found,
            },
        ).sync()
        # ar_tagRes.rd(out_ar.ready & data_arr_read_req.rd)

        out_ar.addr(ar_tagRes.addr)
        out_ar.id(ar_tagRes.id)
        out_ar.len(0)
        self.axiAddrDefaults(out_ar)

        s_r = AxiSBuilder.join_prioritized(self, [
            data_arr_read,
            self.m.r,
        ]).end
        self.s.r(s_r)

    def instantiate_data_array_to_hs(self,
                                     data_arr_r_port: BramPort_withoutClk,
                                     data_arr_w_port: BramPort_withoutClk,
                                    ):
        """
        Convert bram ports of data array to a handshaked interfaces
        """
        data_arr_r_to_hs = RamAsHs()
        data_arr_w_to_hs = RamAsHs()
        data_arr_r_to_hs._updateParamsFrom(data_arr_r_port)
        data_arr_w_to_hs._updateParamsFrom(data_arr_w_port)
        self.data_arr_r_to_hs = data_arr_r_to_hs
        self.data_arr_w_to_hs = data_arr_w_to_hs

        data_arr_r_port(data_arr_r_to_hs.ram)
        data_arr_w_port(data_arr_w_to_hs.ram)

        return data_arr_r_to_hs.r, data_arr_w_to_hs.w

    def data_array_io(self,
                      aw_lru_incr: IndexWayHs,  # out
                      aw_tagRes: AxiCacheTagArrayLookupResIntf,  # in
                      victim_req: AddrHs, victim_way: Handshaked,  # out, in
                      data_arr_read_req: IndexWayHs, data_arr_read: Axi4_r,  # in, out
                      data_arr_r_port: BramPort_withoutClk, data_arr_w_port: BramPort_withoutClk,  # out, out
                      tag_update: AxiCacheTagArrayUpdateIntf  # out
                      ):
        """
        :ivar aw_lru_incr: an interface to increment LRU for write channel
        :ivar victim_req: an interface to get a victim from LRU array for a specified index
        :ivar victim_way: return interface for victim_req
        :ivar aw_tagRes: an interface with a results from tag lookup
        :ivar data_arr_read_req: an input interface with read requests from read section
        :ivar data_arr_read: an output interface with a read data to read section
        :ivar data_arr_r_port: read port of main data array
        :ivar data_arr_w_port: write port of main data array
        """
        # note that the lru update happens even if the data is stalled
        # but that is not a problem because it wont change the order of the usage
        # of the cahceline
        self.incr_lru_on_hit(aw_lru_incr, aw_tagRes)

        st0 = self._reg(
            "victim_load_status0",
            HStruct(
                (self.s.aw.id._dtype, "write_id"),  # the original id and address of a write transaction
                (self.s.aw.addr._dtype, "replacement_addr"),
                (aw_tagRes.TAG_T[aw_tagRes.WAY_CNT], "tags"),
                (BIT, "tag_found"),
                (BIT, "had_empty"),  # had some empty tag
                (aw_tagRes.way._dtype, "found_way"),
                (BIT, "valid"),
            ),
            def_val={
                "valid": 0,
            }
        )
        # resolve if we need to select a victim and optianally ask for it
        st0_ready = self._sig("victim_load_status0_ready")
        has_empty = rename_signal(self, Or(*(~t.valid for t in aw_tagRes.tags)), "has_empty")
        If(st0_ready,
           st0.write_id(aw_tagRes.id),
           st0.replacement_addr(aw_tagRes.addr),
           st0.tags(aw_tagRes.tags),
           st0.tag_found(aw_tagRes.found),
           st0.found_way(aw_tagRes.way),
           st0.had_empty(has_empty),
           # this register is beeing flushed, the values can become invalid
           # the st0.valid is used to detect this state
           st0.valid(aw_tagRes.vld),
        )
        victim_req.addr(self.parse_addr(aw_tagRes.addr)[1])
        tag_check_node = StreamNode(
            [aw_tagRes],
            [victim_req],
            skipWhen={
                victim_req: aw_tagRes.vld & (
                                aw_tagRes.found |
                                has_empty
                            )
            },
            extraConds={
                victim_req:~aw_tagRes.found & ~has_empty
            }
        )

        st1_ready = self._sig("victim_load_status1_ready")
        tag_check_node.sync(~st0.valid | st1_ready)
        tag_check_node_ack = rename_signal(self, tag_check_node.ack(), "tag_check_node_ack")
        st0_ready((st0.valid & tag_check_node_ack & st1_ready) | ~st0.valid | st1_ready)

        victim_load_st = HStruct(
                # and address constructed from an original tag in cache which is beeing replaced
                (self.s.aw.addr._dtype, "victim_addr"),
                # new data to write to data_array
                # (replacement data is still in in_w buffer because it was not consumed
                #  if the tag was not found)
                (aw_tagRes.way._dtype, "victim_way"),
                (self.s.ar.id._dtype, "read_id"),
                (self.s.aw.id._dtype, "write_id"),
                (self.s.aw.addr._dtype, "replacement_addr"),  # the original address used to resolve new tag
                (Bits(2), "data_array_op"),  # type of operation with data_array
            )
        ########################## st1 - pre (read request resolution, victim address resolution) ##############
        d_arr_r, d_arr_w = self.instantiate_data_array_to_hs(
            data_arr_r_port, data_arr_w_port)

        # :note: flush with higher priority than regular read
        need_to_flush = rename_signal(self, st0.valid & (~st0.had_empty & ~st0.tag_found), "need_to_flush")

        If(need_to_flush,
            d_arr_r.addr.data(self.addr_in_data_array(victim_way.data, self.parse_addr(st0.replacement_addr)[1])),
        ).Else(
            d_arr_r.addr.data(self.addr_in_data_array(data_arr_read_req.way, data_arr_read_req.index))
        )
        _victim_way = self._sig("victim_way_tmp", Bits(log2ceil(self.WAY_CNT)))
        _victim_tag = self._sig("victim_tag_tmp", Bits(self.TAG_W))
        SwitchLogic(
            [
                # select first empty tag
                (~tag.valid, [
                    _victim_way(i),
                    _victim_tag(tag.tag),
                ]) for i, tag in enumerate(st0.tags)
            ],
            default=[
                # select an victim specified by victim_way
                _victim_way(victim_way.data),
                SwitchLogic([
                        (victim_way.data._eq(i), _victim_tag(tag.tag))
                        for i, tag in enumerate(st0.tags)
                    ],
                    default=_victim_tag(None)
                )
            ]
        )
        victim_load_status = HObjList(HandshakedReg(HsStructIntf) for _ in range(2))
        for i, st in enumerate(victim_load_status):
            st.T = victim_load_st
            if i == 0:
                st.LATENCY = (1, 2)  # to break a ready chain
        self.victim_load_status = victim_load_status

        st1_in = victim_load_status[0].dataIn.data
        # placed between st0, st1
        pure_write = rename_signal(self, st0.valid & ~need_to_flush & ~data_arr_read_req.vld, "pure_write")
        pure_read = rename_signal(self, ~st0.valid & data_arr_read_req.vld, "pure_read")
        read_plus_write = rename_signal(self, st0.valid & ~need_to_flush & data_arr_read_req.vld, "read_plus_write")
        flush_write = rename_signal(self, st0.valid & need_to_flush & ~data_arr_read_req.vld, "flush_write")
        read_flush_write = rename_signal(self, st0.valid & need_to_flush & data_arr_read_req.vld, "read_flush_write")  # not dispatched at once

        read_req_node = StreamNode(
            [victim_way, data_arr_read_req],
            [d_arr_r.addr, victim_load_status[0].dataIn],
            extraConds={
                victim_way: flush_write | read_flush_write,  # 0
                                   # only write without flush       not write at all but read request
                data_arr_read_req: pure_read | read_plus_write,  # pure_read | read_plus_write, #
                d_arr_r.addr: pure_read | read_plus_write | flush_write | read_flush_write,  # need_to_flush | data_arr_read_req.vld, # 1
                # victim_load_status[0].dataIn: st0.valid | data_arr_read_req.vld,
            },
            skipWhen={
                victim_way: pure_write | pure_read | read_plus_write,
                data_arr_read_req: pure_write | flush_write | read_flush_write,
                d_arr_r.addr: pure_write,
            }
        )
        read_req_node.sync()
        st1_ready(victim_load_status[0].dataIn.rd & read_req_node.ack())

        st1_in.victim_addr(self.deparse_addr(_victim_tag, self.parse_addr(st0.replacement_addr)[1], 0))
        st1_in.victim_way(st0.tag_found._ternary(st0.found_way, _victim_way)),
        st1_in.read_id(data_arr_read_req.id)
        st1_in.write_id(st0.write_id)
        st1_in.replacement_addr(st0.replacement_addr)
        If(pure_write,
            st1_in.data_array_op(data_trans_t.write)
        ).Elif(pure_read,
            st1_in.data_array_op(data_trans_t.read)
        ).Elif(read_plus_write,
            st1_in.data_array_op(data_trans_t.read_and_write)
        ).Else(# .Elif(flush_write | read_flush_write,
            st1_in.data_array_op(data_trans_t.write_and_flush)
        )
        # If(st0.valid,
        #    If(need_to_flush,
        #        st1_in.data_array_op(data_trans_t.write_and_flush)
        #    ).Elif(st0.tag_found & data_arr_read_req.vld,
        #        st1_in.data_array_op(data_trans_t.read_and_write)
        #    ).Else(
        #        st1_in.data_array_op(data_trans_t.write)
        #    )
        # ).Else(
        #    st1_in.data_array_op(data_trans_t.read)
        # )

        victim_load_status[1].dataIn(victim_load_status[0].dataOut)

        self.flush_or_read_node(
            d_arr_r, d_arr_w, victim_load_status[1].dataOut, data_arr_read,
            tag_update)

    def flush_or_read_node(self,
                           d_arr_r: RamHsR,
                           d_arr_w: AddrDataHs,
                           st2_out: HsStructIntf,
                           data_arr_read: Axi4_r,
                           tag_update: AxiCacheTagArrayUpdateIntf,  # out
                           ):
        ########################## st1 - post (victim flushing, read forwarding) ######################
        in_w = AxiSBuilder(self, self.s.w)\
            .buff(self.tag_array.LOOKUP_LATENCY + 4)\
            .end

        st2 = st2_out.data
        d_arr_w.addr(
            self.addr_in_data_array(
                st2.victim_way,
                self.parse_addr(st2.replacement_addr)[1]
            )
        )
        data_arr_read_data = d_arr_r.data  # HsBuilder(self, d_arr_r.data).buff(1, latency=(1, 2)).end
        d_arr_w.data(in_w.data)
        d_arr_w.mask(in_w.strb)

        self.s.b.id(st2.write_id)
        self.s.b.resp(RESP_OKAY)

        data_arr_read.id(st2.read_id)
        data_arr_read.data(data_arr_read_data.data)
        data_arr_read.resp(RESP_OKAY)
        data_arr_read.last(1)

        m = self.m
        m.aw.addr(st2.victim_addr)
        m.aw.id(st2.write_id)
        m.aw.len(0)
        self.axiAddrDefaults(m.aw)

        m.w.data(data_arr_read_data.data)
        m.w.strb(mask(m.w.data._dtype.bit_length() // 8))
        m.w.last(1)

        # flushing needs to have higher priority then read in order
        # to prevent deadlock
        # write replacement after victim load with higher priority
        # else if found just write the data to data array
        is_flush = st2.data_array_op._eq(data_trans_t.write_and_flush)
        contains_write = rename_signal(self, In(st2.data_array_op, [data_trans_t.write,
                                                                    data_trans_t.write_and_flush,
                                                                    data_trans_t.read_and_write]), "contains_write")
        contains_read = rename_signal(self, In(st2.data_array_op, [data_trans_t.read,
                                                                   data_trans_t.write_and_flush,
                                                                   data_trans_t.read_and_write]), "contains_read")
        contains_read_data = rename_signal(self, In(st2.data_array_op, [data_trans_t.read,
                                                                        data_trans_t.read_and_write]), "contains_read_data")

        flush_or_read_node = StreamNode(
            [st2_out,
             data_arr_read_data, in_w],  # collect read data from data array, collect write data
            [data_arr_read,
             m.aw, m.w,
             d_arr_w, self.s.b],  # to read block or to slave connected on "m" interface
                                  # write data to data array and send write acknowledge
            extraConds={
                data_arr_read_data: contains_read,
                in_w: contains_write,

                data_arr_read: contains_read_data,
                m.aw: is_flush,
                m.w: is_flush,
                d_arr_w: contains_write,
                self.s.b: contains_write,
            },
            skipWhen={
                data_arr_read_data:~contains_read,
                in_w:~contains_write,

                data_arr_read:~contains_read_data,
                m.aw:~is_flush,
                m.w:~is_flush,
                d_arr_w:~contains_write,
                self.s.b:~contains_write,
            }
        )
        flush_or_read_node.sync()
        m.b.ready(1)

        tag_update.vld(st2_out.vld & contains_write)
        tag_update.delete(0)
        tag_update.way_en(binToOneHot(st2.victim_way))
        tag_update.addr(st2.replacement_addr)
        # [TODO] initial clean
        lru_array_set = self.lru_array.set
        lru_array_set.addr(None)
        lru_array_set.data(None)
        lru_array_set.vld(0)

    def _impl(self):
        """
        Read operation:

        * Use index to lookup in tag memory
        * if tag matches return cacheline else dispatch read request
          (the transaction is dispatched with original id, uppon data receive the transaction
          is passed to master without any synchronisation with the cache )

        Write operation:

        * Use index to lookup in tag memory
        * If tag matches and the cacheline is not beeing replaced update the data in data array.
        * If tag is not found in corresponding set select a victim and read it from data array, flush it
          and write back cacheline to array and update tag
        """
        # transaction type usind in data array memory access pipeline

        data_array_r, data_array_w = self.data_array.port
        ar_tagRes, aw_tagRes = self.tag_array.lookupRes
        with self._paramsShared():
            data_arr_read = self.data_arr_read = Axi4_r()
            data_arr_read_req = IndexWayHs()
            data_arr_read_req.INDEX_WIDTH = self.INDEX_W
            self.data_arr_read_req = data_arr_read_req

        self.connect_tag_lookup()

        # addd a register with backup register for poential overflow
        # we need this as we need to check if we can store data in advance.
        # this is because we need a higher priority for flushing
        # in order to avoid deadlock.
        _data_arr_read = AxiSBuilder(self, data_arr_read)\
            .buff(1, latency=(1, 2))\
            .end
        _data_arr_read_req = HsBuilder(self, data_arr_read_req)\
            .buff(1, latency=(1, 2))\
            .end

        self.read_handler(
            self.lru_array.incr[0],
            ar_tagRes,
            data_arr_read_req, _data_arr_read)

        self.data_array_io(
            self.lru_array.incr[1],
            aw_tagRes,
            self.lru_array.victim_req, self.lru_array.victim_data,
            _data_arr_read_req, data_arr_read,
            data_array_r, data_array_w,
            self.tag_array.update[0],
        )

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    from hwtLib.xilinx.constants import XILINX_VIVADO_MAX_DATA_WIDTH
    u = AxiCaheWriteAllocWawOnlyWritePropagating()
    u.DATA_WIDTH = 512
    u.CACHE_LINE_SIZE = u.DATA_WIDTH // 8
    u.WAY_CNT = 4
    u.CACHE_LINE_CNT = u.WAY_CNT * 4096
    u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH
    # u.CACHE_LINE_SIZE = 64
    # u.DATA_WIDTH = 512
    # u.WAY_CNT = 2
    # u.CACHE_LINE_CNT = u.WAY_CNT * 4096
    print(to_rtl_str(u))
