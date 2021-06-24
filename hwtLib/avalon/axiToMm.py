#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.constants import READ
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked, HandshakeSync, VectSignal
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.avalon.mm import AvalonMM
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode


class IdLenHs(HandshakeSync):

    def _config(self) -> None:
        self.ID_WIDTH = Param(4)
        self.LEN_WIDTH = Param(6)

    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)
        self.len = VectSignal(self.LEN_WIDTH)
        HandshakeSync._declr(self)


class Axi4_to_AvalonMm(BusBridge):
    """
    Bridge from Axi4 interface to Avalon-MM interface

    :attention: The value of the address must be aligned to the data width.

    .. hwt-autodoc::
    """

    def _config(self) -> None:
        AvalonMM._config(self)
        self.MAX_BURST = 512
        self.ID_WIDTH = Param(4)
        self.RW_PRIORITY = Param(READ)
        self.R_DATA_FIFO_DEPTH = Param(16)
        self.R_SIZE_FIFO_DEPTH = Param(16)

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = Axi4()
            self.m = AvalonMM()._m()

        # a tmp buffer for sizes of read transactions to generate ax.r.last
        f = self.r_size_fifo = HandshakedFifo(IdLenHs)
        f.DEPTH = self.R_DATA_FIFO_DEPTH
        f.LEN_WIDTH = self.s.LEN_WIDTH
        f.ID_WIDTH = self.ID_WIDTH
        if self.MAX_BURST != 2 ** (self.s.LEN_WIDTH + 1):
            raise NotImplementedError(self.MAX_BURST, (2 ** self.s.LEN_WIDTH + 1))

    def connect_r_fifo(self, avalon: AvalonMM, axi: Axi4):
        # buffer for read data to allow forward dispatch of the read requests
        # the availability of the space in fifo is checked using r_data_fifo_capacity counter
        f = HandshakedFifo(Handshaked)
        f.DEPTH = self.R_DATA_FIFO_DEPTH
        f.DATA_WIDTH = self.DATA_WIDTH
        self.r_data_fifo = f

        # f.dataIn.rd ignored because the request should not be dispatched in the first place
        f.dataIn.data(avalon.readData)
        f.dataIn.vld(avalon.readDataValid)

        sf = self.r_size_fifo
        wordIndexCntr = self._reg(
            "wordIndexCntr",
            HStruct(
                (sf.dataOut.len._dtype, "len"),
                (axi.r.id._dtype, "id"),
                (BIT, "vld")
            ),
            def_val={"vld": 0}
        )

        r_out_node = StreamNode([f.dataOut], [axi.r])
        r_out_node.sync(wordIndexCntr.vld)

        # load word index counter if it is invalid else decrement on data transaction
        newSizeAck = (~wordIndexCntr.vld | (wordIndexCntr.len._eq(0) & r_out_node.ack()))
        If(newSizeAck,
            wordIndexCntr.id(sf.dataOut.id),
            wordIndexCntr.len(sf.dataOut.len),
            wordIndexCntr.vld(sf.dataOut.vld),
        ).Elif(r_out_node.ack(),
            wordIndexCntr.len(wordIndexCntr.len - 1),
            wordIndexCntr.vld(wordIndexCntr.len != 0),
        )
        sf.dataOut.rd(newSizeAck)

        axi.r.id(wordIndexCntr.id)
        axi.r.data(f.dataOut.data)
        axi.r.resp(RESP_OKAY)
        axi.r.last(wordIndexCntr.len._eq(0))
        return rename_signal(self, r_out_node.ack(), "r_data_ack")

    def load_addr_tmp(self, addr_tmp: StructIntf, axi_addr: Optional[Axi4_addr]):
        if axi_addr is None:
            return [
                addr_tmp.addr(None),
                addr_tmp.id(None),
                addr_tmp.len(None),
                addr_tmp.len_original(None),
                addr_tmp.is_w(None),
                addr_tmp.vld(0)
            ]
        else:
            return [
                addr_tmp.addr(axi_addr.addr),
                addr_tmp.id(axi_addr.id),
                addr_tmp.len(axi_addr.len),
                addr_tmp.len_original(axi_addr.len),
                addr_tmp.is_w(axi_addr is self.s.aw),
                addr_tmp.vld(1),
            ]

    def _impl(self) -> None:
        avalon: AvalonMM = self.m
        axi = self.s

        addr_tmp = self._reg(
            "addr_tmp",
            HStruct(
                (axi.ar.addr._dtype, "addr"),
                (axi.ar.id._dtype, "id"),
                (axi.ar.len._dtype, "len"),
                (axi.ar.len._dtype, "len_original"),
                (BIT, "vld"),
                (BIT, "is_w"),
            ),
            def_val={"vld": 0}
        )
        r_data_ack = self.connect_r_fifo(avalon, axi)

        # contains the available space in read data fifo
        # used to prevent the dispatch of the reads which would
        # cause overflow of read data fifo
        r_data_fifo_capacity = self._reg(
            "r_data_fifo_capacity",
            Bits(log2ceil(self.R_DATA_FIFO_DEPTH + 1)),
            def_val=self.R_DATA_FIFO_DEPTH)

        will_be_idle = ~addr_tmp.vld | \
                       ~addr_tmp.is_w | \
                            (addr_tmp.vld &
                             addr_tmp.is_w &
                             ~avalon.waitRequest &
                             addr_tmp.len._eq(0) &
                             axi.w.valid &
                             axi.b.ready)
        will_be_idle = rename_signal(self, will_be_idle, "will_be_idle")
        r_size_in = self.r_size_fifo.dataIn
        ar_en = will_be_idle & \
                axi.ar.valid & (r_data_fifo_capacity > fitTo(axi.ar.len, r_data_fifo_capacity)) & \
                r_size_in.rd

        is_w = addr_tmp.vld & addr_tmp.is_w
        ready_for_addr = ~addr_tmp.vld | ~avalon.waitRequest
        addr_tmp_ack = rename_signal(self, ~avalon.waitRequest &
                                           ~(
                                               is_w & ~(axi.w.valid & ((addr_tmp.len != 0) | axi.b.ready))
                                            ), "addr_tmp_ack")
        aw_en = ready_for_addr & axi.w.valid & (~addr_tmp.vld | ~addr_tmp.is_w | (addr_tmp.len != 0) | axi.b.ready)
        is_not_last_w = rename_signal(self, is_w & (addr_tmp.len != 0), "is_not_last_w")
        if self.RW_PRIORITY == READ:
            aw_en = ~axi.ar.valid & aw_en
            ar_en = rename_signal(self, ar_en, "ar_en")
            aw_en = rename_signal(self, aw_en, "aw_en")
            If(ar_en,
                # start new read transaction
                self.load_addr_tmp(addr_tmp, axi.ar)
            ).Elif(~avalon.waitRequest & is_not_last_w & axi.w.valid,
                # finishing write transaction (except last word)
                addr_tmp.len(addr_tmp.len - 1),
            ).Elif(will_be_idle & axi.aw.valid & axi.w.valid,
                # start new write transaction
                self.load_addr_tmp(addr_tmp, axi.aw)
            ).Elif(addr_tmp_ack,
                # all transaction finished, clear addr_tmp register
                self.load_addr_tmp(addr_tmp, None)
            )
        else:
            ar_en = ar_en & \
                ~(is_not_last_w) & \
                ~(axi.aw.valid & axi.w.valid)
            ar_en = rename_signal(self, ar_en, "ar_en")
            aw_en = rename_signal(self, aw_en, "aw_en")
            If(~avalon.waitRequest & is_not_last_w & axi.w.valid,
                # finishing write transaction (except last word)
                addr_tmp.len(addr_tmp.len - 1),
            ).Elif(will_be_idle & axi.aw.valid & axi.w.valid,
                # start new write transaction
                self.load_addr_tmp(addr_tmp, axi.aw)
            ).Elif(ar_en,
                # start new read transaction
                self.load_addr_tmp(addr_tmp, axi.ar)
            ).Elif(addr_tmp_ack,
                # all transaction finished, clear addr_tmp register
                self.load_addr_tmp(addr_tmp, None)
            )

        r_size_in.id(axi.ar.id)
        r_size_in.len(axi.ar.len)
        r_size_in.vld(ar_en)

        If(r_data_ack & ar_en,
            r_data_fifo_capacity(r_data_fifo_capacity - fitTo(axi.ar.len, r_data_fifo_capacity))
        ).Elif(r_data_ack,
            r_data_fifo_capacity(r_data_fifo_capacity + 1)
        ).Elif(ar_en,
            r_data_fifo_capacity(r_data_fifo_capacity - 1 - fitTo(axi.ar.len, r_data_fifo_capacity))
        )
        axi.aw.ready(will_be_idle & aw_en)
        axi.ar.ready(will_be_idle & ar_en)

        avalon.address(addr_tmp.addr)
        avalon.burstCount(fitTo(addr_tmp.len_original, avalon.burstCount) + 1)
        avalon.read(addr_tmp.vld & ~addr_tmp.is_w)
        avalon.write(is_w & axi.w.valid & ((addr_tmp.len != 0) | axi.b.ready))

        avalon.writeData(axi.w.data)
        avalon.byteEnable(axi.w.strb)

        axi.w.ready(
            addr_tmp.vld &
            addr_tmp.is_w &
            ~avalon.waitRequest &
            ((addr_tmp.len != 0) | axi.b.ready)
        )

        axi.b.id(addr_tmp.id)
        axi.b.resp(RESP_OKAY)
        axi.b.valid(addr_tmp.vld &
                    addr_tmp.is_w &
                    ~avalon.waitRequest &
                    axi.w.ready &
                    axi.w.valid &
                    axi.w.last)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Axi4_to_AvalonMm()
    print(to_rtl_str(u))
