#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, List

from hwt.code import Concat, If
from hwt.code_utils import rename_signal
from hwt.hdl.constants import READ, WRITE
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.agents.handshaked import UniversalHandshakedAgent
from hwt.interfaces.agents.universalComposite import UniversalCompositeAgent
from hwt.interfaces.hsStructIntf import HsStructIntf
from hwt.interfaces.std import HandshakeSync, VectSignal, Signal
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtLib.handshaked.ramAsHs import RamAsHs, RamHsR
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.ram import RamSingleClock
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask
from hwt.synthesizer.hObjList import HObjList


class TransRamHsR_addr(HandshakeSync):
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
        
        
class TransRamHsW_addr(TransRamHsR_addr):
    """
    .. hwt-autodoc::
    """
    
    def _config(self):
        TransRamHsR_addr._config(self)
        self.USE_FLUSH = Param(True)

    def _declr(self):
        TransRamHsR_addr._declr(self)
        if(self.USE_FLUSH == True):
            self.flush = Signal()

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalHandshakedAgent(sim, self)


class TransRamHsR(Interface):
    """
    Handshaked RAM port

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.USE_STRB = Param(True)
        TransRamHsR_addr._config(self)

    def _declr(self):
        with self._paramsShared():
            self.addr = TransRamHsR_addr()
            d = self.data = AxiStream(masterDir=DIRECTION.IN)
            d.USE_STRB = False
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)


class TransRamHsW(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)
        TransRamHsW_addr._config(self)

    def _declr(self):
        with self._paramsShared():
            self.addr = TransRamHsW_addr()
            d = self.data = AxiStream()
            d.ID_WIDTH = 0
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)


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

    def _declr_io(self):
        assert self.WORDS_WIDTH % self.DATA_WIDTH == 0
        self.ITEM_WORDS = self.WORDS_WIDTH // self.DATA_WIDTH
        self.WORD_INDEX_MAX = self.ITEM_WORDS - 1

        addClkRstn(self)
        with self._paramsShared():
            self.r = TransRamHsR()
            self.w = TransRamHsW()
            self.flush_data = TransRamHsW()._m()
            self.flush_data.USE_FLUSH = False

    def _declr(self):
        self._declr_io()
        d = self.data_array = RamSingleClock()
        d.MAX_BLOCK_DATA_WIDTH = self.MAX_BLOCK_DATA_WIDTH
        d.DATA_WIDTH = self.DATA_WIDTH
        d.ADDR_WIDTH = self.ADDR_WIDTH + log2ceil(self.ITEM_WORDS)
        d.PORT_CNT = (READ, WRITE)
        d.HAS_BE = True

    def construct_ram_io(self) -> Tuple[RamHsR, AddrDataHs]:
        data_arr_r_port, data_arr_w_port = self.data_array.port
        data_arr_r_to_hs = RamAsHs()
        data_arr_w_to_hs = RamAsHs()
        data_arr_r_to_hs._updateParamsFrom(data_arr_r_port)
        data_arr_w_to_hs._updateParamsFrom(data_arr_w_port)
        self.data_arr_r_to_hs = data_arr_r_to_hs
        self.data_arr_w_to_hs = data_arr_w_to_hs

        data_arr_r_port(data_arr_r_to_hs.ram)
        data_arr_w_port(data_arr_w_to_hs.ram)

        return data_arr_r_to_hs.r, data_arr_w_to_hs.w

    def construct_r_meta(self, flush_req: RtlSignal,
                         read_pending: RtlSignal,
                         r: RamHsR, w: AddrDataHs,
                         w_index: StructIntf,
                         r_index_o: StructIntf) -> HandshakedReg:

        r_meta = HObjList(HandshakedReg(HsStructIntf) for _ in range(2))
        for reg in r_meta:
            reg.LATENCY = 1
            reg.T = HStruct(
                *([(Bits(self.ID_WIDTH), "id")] if self.ID_WIDTH else []),
                (BIT, "flushing"),
                (BIT, "is_last"),
                (BIT, "is_first"),
            )
        self.r_meta = r_meta
        r_meta[1].dataIn(r_meta[0].dataOut)

        r_meta_i = r_meta[0].dataIn.data
        WORD_INDEX_MAX = self.WORD_INDEX_MAX
        w_index_o = w_index
        flush_pending = rename_signal(self, w_index.vld & w_index_o.flushing, "flush_pending")

        def id_copy():
            if self.ID_WIDTH:
                return \
                If(r_meta[0].dataOut.vld,
                   r_meta_i.id(r_meta[0].dataOut.data.id),
                ).Else(
                   r_meta_i.id(r_meta[1].dataOut.data.id),
                )
            else:
                return []

        # begin of entirely new read
        If(flush_pending,
            id_copy(),
            r_meta_i.flushing(1),
            r_meta_i.is_first(0),
            r_meta_i.is_last(w_index_o.word_index._eq(WORD_INDEX_MAX)),
        ).Elif(flush_req & ~read_pending,
            r_meta_i.id(w.addr.id) if self.ID_WIDTH else [],
            r_meta_i.flushing(1),
            r_meta_i.is_first(1),
            r_meta_i.is_last(0),
        ).Else(
            If(read_pending,
               id_copy(),
               r_meta_i.is_first(0),
               r_meta_i.is_last(r_index_o.word_index._eq(WORD_INDEX_MAX)),
            ).Else(
               r_meta_i.id(r.addr.id) if self.ID_WIDTH else [],
               r_meta_i.is_first(1),
               r_meta_i.is_last(0),
            ),
            r_meta_i.flushing(0),
        )

        return r_meta

    def construct_read_part(self,
                            r: TransRamHsR,
                            da_r: RamHsR,
                            r_meta: List[HandshakedReg],
                            flush_req: RtlSignal,
                            read_pending: RtlSignal,
                            r_index_o: StructIntf,
                            r_index_i: StructIntf,
                            w_index_o: StructIntf,
                            flush_data: TransRamHsW):

        r_disp_node = StreamNode(
            [r.addr],
            [da_r.addr, r_meta[0].dataIn, ],
            skipWhen={
                r.addr: flush_req | read_pending,
            },
            extraConds={
                r.addr:~flush_req | ~read_pending,
            }
        )
        r_disp_node.sync()

        If(read_pending,
            da_r.addr.data(Concat(r_index_o.item_index, r_index_o.word_index))
        ).Else(
            da_r.addr.data(Concat(r.addr.addr, r_index_o.word_index._dtype.from_py(0)))
        )

        w = self.w
        If(rename_signal(self, r_disp_node.ack(), "r_disp_ack"),
            If(r_index_o.word_index._eq(0),
                # last item or completly new item
                # [note] flushing has priority
                If(flush_req,
                    # begin of the read for flush
                    r_index_i.item_index(w.addr.addr),
                    r_index_i.vld(1),
                ).Else(
                    # begin of the normal read
                    r_index_i.item_index(r.addr.addr),
                    r_index_i.vld(r.addr.vld),
                ),
                r_index_i.word_index(1),
            ).Elif(r_index_o.word_index._eq(self.WORD_INDEX_MAX),
                # first addr and data is skipping this reg
                # this means that tere has to be 1 clk of vld=0 for this first word to pass
                r_index_i.word_index(0),
                r_index_i.vld(0),
            ).Else(
                # pass next word of item
                r_index_i.word_index(r_index_o.word_index + 1),
                r_index_i(r_index_o, exclude=[r_index_i.word_index]),
            )
        )
        _r_meta_o = r_meta[1].dataOut
        r_meta_o = _r_meta_o.data
        StreamNode(
            [da_r.data, _r_meta_o],
            [r.data, flush_data.addr, flush_data.data],
            skipWhen={
                r.data: _r_meta_o.vld & r_meta_o.flushing,
                flush_data.data: _r_meta_o.vld & ~r_meta_o.flushing,
                flush_data.addr: _r_meta_o.vld & (~r_meta_o.flushing | ~r_meta_o.is_first),
            },
            extraConds={
                r.data:~r_meta_o.flushing,
                flush_data.data: r_meta_o.flushing,
                flush_data.addr: r_meta_o.flushing & r_meta_o.is_first,
            },
        ).sync()

        if self.ID_WIDTH:
            flush_data.addr.id(r_meta_o.id)
        flush_data.addr.addr(w_index_o.item_index)
        flush_data.data.data(da_r.data.data)
        flush_data.data.strb(mask(flush_data.data.strb._dtype.bit_length()))
        flush_data.data.last(r_meta_o.is_last)

        if self.ID_WIDTH:
            r.data.id(r_meta_o.id)
        r.data.data(da_r.data.data)
        r.data.last(r_meta_o.is_last)

    def construct_write_part(self, w: TransRamHsW,
                             da_w: AddrDataHs,
                             w_index_i: StructIntf,
                             w_index_o, r_index_o,
                             da_r: RamHsR,
                             r_meta_din: HsStructIntf):
        WORD_INDEX_MAX = self.WORD_INDEX_MAX

        write_pending = r_index_o.vld
        w_disp_node = StreamNode(
            [w.addr, w.data],
            [da_w, ],
            skipWhen={
                # dissable address input if finishing peding transaction
                w.addr: write_pending,
            },
            extraConds={
                # stall if pending read and flush required
                w.addr: rename_signal(self, ~write_pending & (w.addr.vld & ~w.addr.flush) | (~r_index_o.vld & da_r.addr.rd & r_meta_din.rd), "w_addr_en"),
                # dissable input write data if no wirite transaction is pending or will be pending
                w.data: write_pending | (w.addr.vld & (~w.addr.flush | ~r_index_o.vld)),
            },
        )
        w_disp_node.sync()
        w_disp_ack = rename_signal(self, w_disp_node.ack(), "w_disp_ack")
        If(w_disp_ack,
            If(w_index_o.word_index._eq(0),
                # completly new item
                w_index_i.item_index(w.addr.addr),
                w_index_i.flushing(w.addr.flush),
                w_index_i.word_index(1),
                w_index_i.vld(w.addr.vld),  # start of a new
            ).Elif(w_index_o.word_index._eq(WORD_INDEX_MAX),
                # last item
                w_index_i.word_index(0),
                w_index_i.vld(0),  # just finished
            ).Else(
                # pass next word of item
                w_index_i.word_index(w_index_o.word_index + 1),
                w_index_i(w_index_o, exclude=[w_index_i.word_index]),
            )
        )

        If(write_pending,
           da_w.addr(Concat(w_index_o.item_index, w_index_o.word_index))
        ).Else(
           da_w.addr(Concat(w.addr.addr, w_index_o.word_index._dtype.from_py(0)))
        )
        da_w.mask(w.data.strb)
        da_w.data(w.data.data)

    def _impl(self):
        r_index = self._reg("r_index",
            HStruct(
                (Bits(self.ADDR_WIDTH), "item_index"),
                (Bits(log2ceil(self.ITEM_WORDS)), "word_index"),
                (BIT, "vld"),
            ),
            def_val={
                "vld": 0,
                "word_index": 0
            }
        )
        w_index = self._reg("w_index",
            HStruct(
                *r_index._dtype.fields,
                (BIT, "flushing"),
            ),
            def_val={
                "vld": 0,
                "word_index": 0
            }
        )

        r_index_i, r_index_o = r_index, r_index
        w_index_i, w_index_o = w_index, w_index
        w = self.w
        flush_req = w.addr.vld & w.addr.flush
        read_pending = r_index.vld

        da_r, da_w = self.construct_ram_io()
        r_meta = self.construct_r_meta(flush_req, read_pending, self.r, self.w, w_index, r_index_o)
        self.construct_read_part(self.r, da_r, r_meta, flush_req, read_pending,
                                 r_index_o, r_index_i, w_index_o, self.flush_data)
        self.construct_write_part(w, da_w, w_index_i, w_index_o, r_index_o, da_r, r_meta[0].dataIn)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RamTransactional()
    # u.ID_WIDTH = 2
    u.DATA_WIDTH = 32
    u.ADDR_WIDTH = 16
    u.WORDS_WIDTH = 64
    u.ITEMS = 32
    print(to_rtl_str(u))
