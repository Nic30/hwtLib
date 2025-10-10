#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Or, Concat
from hwt.code_utils import rename_signal
from hwt.constants import WRITE, READ
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.std import HwIOVectSignal, HwIODataRdVld, HwIORdVldSync
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.arrayQuery import flatten, grouper
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi_comp.cache.addrTypeConfig import CacheAddrTypeConfig
from hwtLib.amba.axi_comp.cache.pseudo_lru import PseudoLru
from hwtLib.commonHwIO.addr import HwIOAddrRdVld
from hwtLib.commonHwIO.addr_data import HwIOAddrDataRdVld
from hwtLib.logic.binToOneHot import binToOneHot
from hwtLib.mem.ramXor import RamXorSingleClock


# extract variant with id
class HwIOIndexWayRdVld(HwIORdVldSync):

    @override
    def hwConfig(self):
        self.ID_WIDTH = HwParam(0)
        self.INDEX_WIDTH = HwParam(10)
        self.WAY_CNT = HwParam(4)

    @override
    def hwDeclr(self):
        if self.ID_WIDTH:
            self.id = HwIOVectSignal(self.ID_WIDTH)
        self.index = HwIOVectSignal(self.INDEX_WIDTH)
        if self.WAY_CNT > 1:
            self.way = HwIOVectSignal(log2ceil(self.WAY_CNT - 1))
        HwIORdVldSync.hwDeclr(self)


class AxiCacheLruArray(CacheAddrTypeConfig):
    """
    A memory storing Tree-PLRU records with multiple ports.
    The access using various ports is merged together.
    The victim_req port also marks the way as lastly used.
    The set port disables all discards all pending updates
    and it is meant to be used for an initialization of the array/cache.

    .. figure:: ./_static/AxiCacheLruArray.png

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        CacheAddrTypeConfig.hwConfig(self)
        self.INCR_PORT_CNT = HwParam(2)
        self.WAY_CNT = HwParam(4)

    def _compute_constants(self):
        assert self.WAY_CNT >= 1, self.WAY_CNT
        self._compupte_tag_index_offset_widths()
        self.LRU_WIDTH = PseudoLru.lru_reg_width(self.WAY_CNT)

    @override
    def hwDeclr(self):
        self._compute_constants()
        addClkRstn(self)
        # used to initialize the LRU data (in the case of cache reset)
        # while set port is active all other ports are blocked
        s = self.set = HwIOAddrDataRdVld()
        s.ADDR_WIDTH = self.INDEX_W
        s.DATA_WIDTH = self.LRU_WIDTH

        # used to increment the LRU data in the case of hit
        self.incr = HwIOArray(HwIOIndexWayRdVld() for _ in range(self.INCR_PORT_CNT))
        for i in self.incr:
            i.INDEX_WIDTH = self.INDEX_W
            i.WAY_CNT = self.WAY_CNT

        # get a victim for a selected cacheline index
        # The cacheline returned as a victim is also marked as used just now
        vr = self.victim_req = HwIOAddrRdVld()
        vr.ADDR_WIDTH = self.INDEX_W
        vr.ID_WIDTH = 0
        vd = self.victim_data = HwIODataRdVld()._m()
        vd.DATA_WIDTH = log2ceil(self.WAY_CNT - 1)

        m = self.lru_mem = RamXorSingleClock()
        m.ADDR_WIDTH = self.INDEX_W
        m.DATA_WIDTH = self.LRU_WIDTH
        m.PORT_CNT = (
            # victim_req preload, victim_req write back or set,
            READ, WRITE,
            #  incr preload, incr write back...
            *flatten((READ, WRITE) for _ in range(self.INCR_PORT_CNT))
        )

    def merge_successor_writes_into_incr_one_hot(self, succ_writes, incr_val_oh):
        if succ_writes:
            for succ_write_vld, succ_write_oh in succ_writes:
                en_mask = Concat(*[succ_write_vld for _ in range(succ_write_oh._dtype.bit_length())])
                incr_val_oh = incr_val_oh | (succ_write_oh & en_mask)
        return incr_val_oh

    @override
    def hwImpl(self):
        m = self.lru_mem
        victim_req_r, victim_req_w = m.port[:2]

        # victim selection ports
        victim_req = self.victim_req
        victim_req_r.en(victim_req.vld)
        victim_req_r.addr(victim_req.addr)
        victim_req_tmp = self._reg(
            "victim_req_tmp",
            HStruct(
              (victim_req.addr._dtype, "index"),
              (BIT, "vld")
            ),
            def_val={"vld": 0}
        )
        set_ = self.set
        victim_data = self.victim_data
        victim_req.rd(~set_.vld & (~victim_req_tmp.vld | victim_data.rd))
        If((~victim_req_tmp.vld | victim_data.rd) & ~set_.vld,
           victim_req_tmp.index(victim_req.addr),
           victim_req_tmp.vld(victim_req.vld),
        )

        incr_rw = list(grouper(2, m.port[2:]))

        # in the first stp we have to collect all pending addresses
        # because we need it in order to resolve any potential access merging
        incr_tmp_mask_oh = []
        for i, (incr_in, (incr_r, _)) in enumerate(zip(self.incr, incr_rw)):
            incr_tmp = self._reg(
                f"incr_tmp{i:d}",
                HStruct(
                    (incr_in.index._dtype, "index"),
                    (incr_in.way._dtype, "way"),
                    (BIT, "vld")
                ),
                def_val={"vld": 0}
            )
            incr_tmp.index(incr_in.index)
            incr_tmp.way(incr_in.way)
            incr_tmp.vld(incr_in.vld & ~set_.vld)

            incr_val_oh = rename_signal(self, binToOneHot(incr_in.way), f"incr_val{i:d}_oh")
            incr_tmp_mask_oh.append((incr_tmp, incr_val_oh))

        lru = PseudoLru(victim_req_r.dout)
        victim = rename_signal(self, lru.get_lru(), "victim")
        victim_oh = rename_signal(self, binToOneHot(victim), "victim_oh")

        victim_data.data(victim)
        victim_data.vld(victim_req_tmp.vld & ~set_.vld)

        succ_writes = [
            (incr2_tmp.vld & incr2_tmp.index._eq(victim_req_tmp.index), incr2_val_oh)
            for incr2_tmp, incr2_val_oh in incr_tmp_mask_oh
        ]
        _victim_oh = self.merge_successor_writes_into_incr_one_hot(succ_writes, victim_oh)
        _victim_oh = rename_signal(self, _victim_oh, f"victim_val{i:d}_oh_final")

        set_.rd(1)
        If(set_.vld,
            # repurpose victim req victim_req_w port for an intialization of LRU array using "set" port
            victim_req_w.en(1),
            victim_req_w.addr(set_.addr),
            victim_req_w.din(set_.data),
        ).Else(
            # use victim_req_w port for a victim req write back as usuall
            victim_req_w.en(victim_req_tmp.vld),
            victim_req_w.addr(victim_req_tmp.index),
            victim_req_w.din(lru.mark_use_many(_victim_oh)),
        )

        for i, (incr_in, (incr_r, incr_w), (incr_tmp, incr_val_oh)) in enumerate(zip(self.incr, incr_rw, incr_tmp_mask_oh)):
            # drive incr_r port
            incr_r.addr(incr_in.index)
            incr_r.en(incr_in.vld)
            incr_in.rd(~set_.vld)

            # resolve the final mask of LRU incrementation for this port and drive incr_w
            prev_writes = [
                    victim_req_tmp.vld & victim_req_tmp.index._eq(incr_tmp.index)
                ] + [
                    incr2_tmp.vld & incr2_tmp.index._eq(incr_tmp.index)
                    for incr2_tmp, _ in incr_tmp_mask_oh[:i]
                ]
            # if any of previous port writes to same index we need to ommit this write as it is writen by some previous port
            incr_w.addr(incr_tmp.index)
            incr_w.en(incr_tmp.vld & ~Or(*prev_writes) & ~set_.vld)

            succ_writes = [
                (incr2_tmp.vld & incr2_tmp.index._eq(incr_tmp.index), incr2_val_oh)
                for incr2_tmp, incr2_val_oh in incr_tmp_mask_oh[i + 1:]
            ]

            # if collides with others merge the incr_val_oh
            incr_val_oh = self.merge_successor_writes_into_incr_one_hot(succ_writes, incr_val_oh)
            incr_val_oh = rename_signal(self, incr_val_oh, f"incr_val{i:d}_oh_final")
            incr_w.din(PseudoLru(incr_r.dout).mark_use_many(incr_val_oh))

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    u = AxiCacheLruArray()
    print(to_rtl_str(u))
