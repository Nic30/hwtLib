#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.constants import READ, WRITE
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.agents.handshaked import UniversalHandshakedAgent
from hwt.interfaces.hsStructIntf import HsStructIntf
from hwt.interfaces.std import HandshakeSync, VectSignal, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.handshaked.ramAsHs import RamHsRAgent, RamAsHs
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.ram import RamSingleClock
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask


class RamHsR_addr(HandshakeSync):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(0)
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)
        self.addr = VectSignal(self.ADDR_WIDTH)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalHandshakedAgent(sim, self)


class RamHsR(Interface):
    """
    Handshaked RAM port

    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(0)
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        with self._paramsShared():
            self.addr = RamHsR_addr()
            d = self.data = AxiStream(masterDir=DIRECTION.IN)
            d.USE_STRB = False
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RamHsRAgent(sim, self)


class RamHsW_addr(RamHsR_addr):

    def _declr(self):
        self.flush = Signal()
        RamHsR_addr._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalHandshakedAgent(sim, self)


class RamHsW(RamHsR_addr):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)
        RamHsR_addr._config(self)

    def _declr(self):
        with self._paramsShared():
            self.addr = RamHsW_addr()
            d = self.data = AxiStream()
            d.ID_WIDTH = 0
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


class RamTransactional(Unit):
    """
    A RAM with 1 read port and 1 write port with flush before functionality.
    If the flush is activate the current data is read first before it is overwritten by write data.

    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(8)  # address has the granularity of the item
        self.DATA_WIDTH = Param(8)
        self.WORDS_WIDTH = Param(16)
        self.MAX_BLOCK_DATA_WIDTH = Param(None)

    def _declr(self):
        assert self.WORDS_WIDTH % self.DATA_WIDTH == 0
        self.ITEM_WORDS = self.WORDS_WIDTH // self.DATA_WIDTH
        addClkRstn(self)
        with self._paramsShared():
            self.r = RamHsR()
            self.w = RamHsW()
            self.flush_data = RamHsW()._m()

        d = self.data_array = RamSingleClock()
        d.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        d.DATA_WIDTH = self.DATA_WIDTH
        d.ADDR_WIDTH = self.ADDR_WIDTH + log2ceil(self.ITEM_WORDS)
        d.PORT_CNT = (READ, WRITE)
        d.HAS_BE = True

    def _impl(self):
        data_arr_r_port, data_arr_w_port = self.data_array.port
        data_arr_r_to_hs = RamAsHs()
        data_arr_w_to_hs = RamAsHs()
        data_arr_r_to_hs._updateParamsFrom(data_arr_r_port)
        data_arr_w_to_hs._updateParamsFrom(data_arr_w_port)
        self.data_arr_r_to_hs = data_arr_r_to_hs
        self.data_arr_w_to_hs = data_arr_w_to_hs

        data_arr_r_port(data_arr_r_to_hs.ram)
        data_arr_w_port(data_arr_w_to_hs.ram)

        da_r, da_w = data_arr_r_to_hs.r, data_arr_w_to_hs.w
        INDEX_SUFFIX_MAX = self.ITEM_WORDS - 1

        # r_index = HandshakedReg(HsStructIntf)
        # r_index.T = HStruct(
        #     (Bits(self.ADDR_WIDTH), "index_prefix"),
        #     (Bits(log2ceil(self.ITEM_WORDS)), "index_suffix"),
        # )
        # self.r_index = r_index

        # w_index = HandshakedReg(HsStructIntf)
        # w_index.T = HStruct(
        #    *r_index_t.fields,
        #    (BIT, "flushing"),
        # )
        # self.w_index = w_index

        r_index = self._reg("r_index", HStruct(
                (Bits(self.ADDR_WIDTH), "index_prefix"),
                (Bits(log2ceil(self.ITEM_WORDS)), "index_suffix"),
                (BIT, "vld"),
            ), def_val={"vld": 0,
                        "index_suffix": INDEX_SUFFIX_MAX})
        w_index = self._reg("w_index", HStruct(
                *r_index._dtype.fields,
                (BIT, "flushing"),
            ), def_val={"vld": 0,
                        "index_suffix": INDEX_SUFFIX_MAX})

        r_index_i, r_index_o = r_index, r_index
        w_index_i, w_index_o = w_index, w_index

        # r_index_i, r_index_o = r_index.dataIn.data, r_index.dataOut.data
        # w_index_i, w_index_o = w_index.dataIn.data, w_index.dataOut.data

        r_meta = HandshakedReg(HsStructIntf)
        r_meta.T = HStruct(
            *([(Bits(self.ID_WIDTH), "id")] if self.ID_WIDTH else []),
            (BIT, "flushing"),
            (BIT, "is_last"),
            (BIT, "is_first"),
        )
        self.r_meta = r_meta
        r_meta_i, r_meta_o = r_meta.dataIn.data, r_meta.dataOut.data
        r, w = self.r, self.w
        flush_req = w.addr.vld & w.addr.flush

        read_pending = r_index.vld
        read_begin = ~read_pending | r_index_o.index_suffix._eq(INDEX_SUFFIX_MAX)
        r_disp_node = StreamNode(
            [r.addr],
            [da_r.addr,
             r_meta.dataIn,  # r_index.dataIn
             ],
            skipWhen={
                r.addr: flush_req | (read_pending & (r_index_o.index_suffix != INDEX_SUFFIX_MAX)),
            },
            extraConds={
                r.addr:~flush_req | read_begin,
            }
        )
        r_disp_node.sync()
        If(read_begin,
            da_r.addr.data(Concat(r.addr.addr, r_index_o.index_suffix._dtype.from_py(0)))
        ).Else(
            da_r.addr.data(Concat(r_index_o.index_prefix, r_index_o.index_suffix))
        )

        flush_pending = w_index.vld & w_index_o.flushing
        # begin of entirely new read
        If(flush_pending,
            r_meta_i.id(r_meta_o.id) if self.ID_WIDTH else [],
            r_meta_i.flushing(1),
            r_meta_i.is_last(w_index_o.index_suffix._eq(INDEX_SUFFIX_MAX)),
            r_meta_i.is_first(0),
        ).Elif(flush_req & ~read_pending,
            r_meta_i.id(w.addr.id) if self.ID_WIDTH else [],
            r_meta_i.is_first(1),
            r_meta_i.flushing(1),
            r_meta_i.is_last(0),
        ).Else(
            If(read_pending,
               r_meta_i.id(r_meta_o.id) if self.ID_WIDTH else [],
               r_meta_i.is_first(0),
               r_meta_i.is_last(r_index_o.index_suffix._eq(INDEX_SUFFIX_MAX)),
            ).Else(
               r_meta_i.id(r.addr.id) if self.ID_WIDTH else [],
               r_meta_i.is_last(0),
               r_meta_i.is_first(1),
            ),
            r_meta_i.flushing(0),
        )

        If(r_disp_node.ack(),
            If(r_index_o.index_suffix != INDEX_SUFFIX_MAX,
                # pass next word of item
                r_index_i.index_suffix(r_index_o.index_suffix + 1),
                r_index_i(r_index_o, exclude=[r_index_i.index_suffix]),
            ).Else(
                # last item or completly new item
                If(w.addr.vld & w.addr.flush,
                    r_index_i.index_prefix(w.addr.addr),
                    r_index_i.vld(1),
                ).Else(
                    r_index_i.index_prefix(r.addr.addr),
                    r_index_i.vld(r.addr.vld),
                ),
                r_index_i.index_suffix(1),
            )
        )

        flush_data = self.flush_data
        StreamNode(
            [da_r.data, r_meta.dataOut],
            [r.data, flush_data.addr, flush_data.data],
            skipWhen={
                r.data: r_meta.dataOut.vld & r_meta_o.flushing,
                flush_data.data: r_meta.dataOut.vld & ~r_meta_o.flushing,
                flush_data.addr: r_meta.dataOut.vld & (~r_meta_o.flushing | ~r_meta_o.is_first),
            },
            extraConds={
                r.data:~r_meta_o.flushing,
                flush_data.data: r_meta_o.flushing,
                flush_data.addr: r_meta_o.flushing & r_meta_o.is_first,
            },
        ).sync()
        flush_data.addr.addr(w_index_o.index_prefix)
        if self.ID_WIDTH:
            flush_data.addr.id(r_meta_o.id)
        flush_data.addr.flush(1)
        flush_data.data.strb(mask(flush_data.data.strb._dtype.bit_length()))
        flush_data.data.data(da_r.data.data)
        flush_data.data.last(r_meta_o.is_last)

        if self.ID_WIDTH:
            r.data.id(r_meta_o.id)
        r.data.data(da_r.data.data)
        r.data.last(r_meta_o.is_last)

        write_pending = w_index.vld
        w_disp_node = StreamNode(
            [w.addr, w.data],
            [da_w,  # w_index.dataIn
             ],
            skipWhen={
                w.addr: write_pending,  # dissable address input if finishing peding transaction
            },
            extraConds={
                w.addr:~w.addr.flush | (da_r.addr.rd & r_meta.dataIn.rd)  # stall if pending read and flush required
            },
        )
        w_disp_node.sync()

        If(w_disp_node.ack(),
            If(r_index_o.index_suffix != INDEX_SUFFIX_MAX,
                # pass next word of item
                w_index_i.index_suffix(w_index_o.index_suffix + 1),
                w_index_i(w_index_o, exclude=[w_index_i.index_suffix]),
            ).Else(
                # completly new item
                w_index_i.index_prefix(w.addr.addr),
                w_index_i.vld(w.addr.vld),
                w_index_i.index_suffix(1),
            )
        )

        If(~write_pending,
           da_w.addr(Concat(w.addr.addr, w_index_o.index_suffix._dtype.from_py(0)))
        ).Else(
           da_w.addr(Concat(w_index_o.index_prefix, w_index_o.index_suffix))
        )
        da_w.mask(w.data.strb)
        da_w.data(w.data.data)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RamTransactional()
    #u.ID_WIDTH = 2
    u.DATA_WIDTH = 32
    u.ADDR_WIDTH = 16
    u.WORDS_WIDTH = 64
    u.ITEMS = 32
    print(to_rtl_str(u))
