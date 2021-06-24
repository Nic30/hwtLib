#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import HandshakeSync, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.axi4Lite import Axi4Lite, Axi4Lite_addr
from hwtLib.amba.axi_comp.buff import AxiBuff
from hwtLib.amba.constants import PROT_DEFAULT
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from typing import Optional


class HandshakedIdAndLen(HandshakeSync):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(4)
        self.LEN_WIDTH = Param(8)

    def _declr(self):
        if self.ID_WIDTH > 0:
            self.id = VectSignal(self.ID_WIDTH)
        self.len = VectSignal(self.LEN_WIDTH)
        super(HandshakedIdAndLen, self)._declr()


class Axi_to_AxiLite(BusBridge):
    """
    AXI3/4 -> Axi4Lite bridge

    :attention: AXI interfaces works in read first mode, overlapping transactions
        are not checked to end up in proper r/w order
    :attention: only last response code on AxiLite for transaction is used as a response code for Axi4
        That means if the error appears somewhere in middle beat of the transaction the error is ignored
    :ivar ~.MAX_TRANS_OVERLAP: depth of internal FIFO which is used to allow the transactions
        to overlap each other in order to pipeline the execution of transactions

    .. hwt-autodoc::
    """

    def __init__(self, intfCls=Axi4, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(Axi_to_AxiLite, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        self.intfCls._config(self)
        self.MAX_TRANS_OVERLAP = Param(4)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = self.intfCls()
            self.m = Axi4Lite()._m()

        # *_req_fifo are used to aviod blocking during addr/data/confirmation waiting on axi channels
        r_f = self.r_req_fifo = HandshakedFifo(HandshakedIdAndLen)
        w_f = self.w_req_fifo = HandshakedFifo(HandshakedIdAndLen)
        for f in [w_f, r_f]:
            f.ID_WIDTH = self.ID_WIDTH
            f.LEN_WIDTH = self.intfCls.LEN_WIDTH
            f.DEPTH = self.MAX_TRANS_OVERLAP

        with self._paramsShared():
            self.out_reg = AxiBuff(Axi4Lite)
            self.in_reg = AxiBuff(self.intfCls)
            self.in_reg.DATA_BUFF_DEPTH = \
                self.in_reg.ADDR_BUFF_DEPTH = \
                self.out_reg.DATA_BUFF_DEPTH = \
                self.out_reg.ADDR_BUFF_DEPTH = 1

    def gen_addr_logic(self, addr_ch_in: Axi4_addr,
                       addr_ch_out: Axi4Lite_addr,
                       req_fifo_inp: HandshakedIdAndLen):
        """
        Instanciate logic which splits the transactions to a beats on AxiLite interface
        and propagate informations about the transacttions to req_fifo_inp for later use
        """
        name_prefix = addr_ch_in._name + "_"
        len_rem = self._reg(name_prefix + "len_rem", addr_ch_in.len._dtype, def_val=0)
        # len_rem_vld is valid only if len > 0 otherwise transaction is processed
        # without lem_rem care
        len_rem_vld = self._reg(name_prefix + "len_rem_vld", def_val=0)
        addr_step = self.DATA_WIDTH // 8
        actual_addr = self._reg(name_prefix + "actual_addr", addr_ch_in.addr._dtype)

        If(len_rem_vld,
            addr_ch_out.addr(actual_addr),
            addr_ch_in.ready(0),  # because we need to process pending req. first
            addr_ch_out.valid(1),
            If(addr_ch_out.ready,
                # move on next beat
                actual_addr(actual_addr + addr_step),
                If(len_rem._eq(0),
                   len_rem_vld(0),
                ),
                len_rem(len_rem - 1),
            ),
        ).Else(
            addr_ch_out.addr(addr_ch_in.addr),
            # have to store request to register if it is longer than
            # a single beat
            actual_addr(addr_ch_out.addr + addr_step),
            len_rem(addr_ch_in.len - 1),
            len_rem_vld(addr_ch_in.valid & (addr_ch_in.len != 0) & addr_ch_out.ready & req_fifo_inp.rd),
            # directly pass this first beat
            StreamNode([addr_ch_in], [addr_ch_out]).sync(req_fifo_inp.rd),
        )
        addr_ch_out.prot(PROT_DEFAULT)
        # push new request to req_fifo only on start of new requirest
        req_fifo_inp.vld(~len_rem_vld & addr_ch_in.valid & addr_ch_out.ready)
        if self.ID_WIDTH:
            req_fifo_inp.id(addr_ch_in.id)
        req_fifo_inp.len(addr_ch_in.len)

    def gen_w_logic(self, w_in, w_out):
        """
        Directly connect the w channels with ignore of extra signals
        (The data should be already synchronized by order of beats on channel)
        """
        ignored = {w_in.last}
        if hasattr(w_in, "id"):
            ignored.add(w_in.id)
        w_out(w_in, exclude=ignored)

    def gen_b_or_r_logic(self, inp, outp, fifo_out, propagete_only_on_last):
        """
        Use counter to skip intermediate generated transactions
        and pass only confirmation from last beat of the original transaction
        """
        name_prefix = outp._name
        rem = self._reg(name_prefix + "rem", self.s.aw.len._dtype)
        if self.ID_WIDTH:
            id_tmp = self._reg(name_prefix + "id_tmp", outp.id._dtype)
        rem_vld = self._reg(name_prefix + "rem_vld", def_val=0)

        StreamNode(
            [inp],
            [outp],
            extraConds={
                outp: rem_vld & rem._eq(0) if propagete_only_on_last else rem_vld,
                inp: rem_vld,
            }
        ).sync()

        If(rem_vld,
            fifo_out.rd(inp.valid & outp.ready & rem._eq(0)),
            If(inp.valid & outp.ready,
                # now processing next beat
                If(rem != 0,
                    # this was not the last beat
                    rem(rem - 1)
                ).Elif(fifo_out.vld,
                    # this was the last beat and we can directly start new one
                    rem(fifo_out.len),
                    id_tmp(fifo_out.id) if self.ID_WIDTH else [],
                ).Else(
                    # this was the last beat and there is no next transaction
                    rem_vld(0),
                )
            ),
        ).Else(
            # in iddle store the information from b_fifo
            rem(fifo_out.len),
            id_tmp(fifo_out.id) if self.ID_WIDTH else [],
            rem_vld(fifo_out.vld),
            fifo_out.rd(1),
        )
        already_connected = {outp.valid, outp.ready}
        if self.ID_WIDTH:
            outp.id(id_tmp)
            already_connected.add(outp.id)

        if hasattr(outp, "last"):
            outp.last(rem._eq(0) & rem_vld)
            already_connected.add(outp.last)
        outp(inp, exclude=already_connected)

    def _impl(self):
        m, s = self.in_reg.m, self.out_reg.s
        w_fifo, r_fifo = self.w_req_fifo, self.r_req_fifo
        propagateClkRstn(self)

        self.in_reg.s(self.s)

        self.gen_addr_logic(m.ar, s.ar, r_fifo.dataIn)
        self.gen_addr_logic(m.aw, s.aw, w_fifo.dataIn)
        self.gen_w_logic(m.w, s.w)
        self.gen_b_or_r_logic(s.r, m.r, r_fifo.dataOut, False)
        self.gen_b_or_r_logic(s.b, m.b, w_fifo.dataOut, True)

        self.m(self.out_reg.m)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Axi_to_AxiLite()
    print(to_rtl_str(u))
