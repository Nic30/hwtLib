#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import READ
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.cesnet.mi32.intf import Mi32


class Axi4Lite_to_Mi32(BusBridge):
    """
    Bridge from AxiLite interface to MI32 interface

    .. hwt-autodoc::
    """

    def _config(self) -> None:
        Mi32._config(self)
        self.RW_PRIORITY = Param(READ)

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = Axi4Lite()
            self.m = Mi32()._m()

    def _impl(self) -> None:
        mi32 = self.m
        axi = self.s

        addr = self._reg("addr", axi.ar.addr._dtype)
        addr_vld = self._reg("addr_vld", def_val=0)
        addr_w = self._reg("addr_w", def_val=0)
        addr_ack = self._sig("addr_ack")
        r_data = self._reg("r_data", axi.r.data._dtype)
        r_data_vld = self._reg("r_data_vld", def_val=0)

        # this is required as we can not notify to MI32 slave that the axi master is not
        # able to receive data
        r_transaction_pending = self._reg("r_transaction_pending", def_val=0)
        w_transaction_pending = self._reg("w_transaction_pending", def_val=0)
        #backpressure = self._sig("backpressure")
        r_trans_ack = axi.r.ready & r_data_vld
        axi_w_ready_tmp = self._sig("axi_w_ready_tmp")
        w_trans_ack = addr_vld & addr_w & mi32.ardy & axi_w_ready_tmp
        no_transaction = (
            ~r_transaction_pending | r_trans_ack
        ) & (
            ~w_transaction_pending | w_trans_ack
        )
        idle =  no_transaction #& ~backpressure
        ready_for_addr = ~addr_vld | addr_ack
        if self.RW_PRIORITY == READ:
            If(idle & axi.ar.valid,
                addr(axi.ar.addr),
                addr_vld(1),
                addr_w(0),
            ).Elif(idle & axi.aw.valid,
                addr(axi.aw.addr),
                addr_vld(1),
                addr_w(1),
            ).Elif(addr_ack,
                addr(None),
                addr_vld(0),
                addr_w(None),   
            )
            axi.ar.ready(idle & ready_for_addr)
            axi.aw.ready(idle & (~axi.ar.valid & ready_for_addr))
            If(r_trans_ack,
                r_transaction_pending(axi.ar.valid)
            )
            If(w_trans_ack,
                w_transaction_pending(~axi.ar.valid & axi.aw.valid)
            )
        else:
            If(idle & axi.aw.valid,
                addr(axi.aw.addr),
                addr_vld(1),
                addr_w(1),
            ).Elif(idle & axi.ar.valid,
                addr(axi.ar.addr),
                addr_vld(1),
                addr_w(0),
            ).Elif(addr_ack,
                addr(None),
                addr_vld(0),
                addr_w(None),
            )
            axi.aw.ready(idle & ready_for_addr)
            axi.ar.ready(idle & ~axi.aw.valid & ready_for_addr)
            If(r_trans_ack,
                r_transaction_pending(~axi.aw.valid & axi.ar.valid)
            )
            If(w_trans_ack,
                w_transaction_pending(axi.aw.valid)
            )

        mi32.rd(idle & addr_vld & ~addr_w)
        mi32.wr(idle & addr_vld & addr_w & axi.w.valid)
        mi32.addr(addr)
        addr_ack(mi32.ardy)
        mi32.dwr(axi.w.data)
        mi32.be(axi.w.strb)
        axi_w_ready_tmp(addr_vld & addr_w & mi32.ardy)
        axi.w.ready(axi_w_ready_tmp)
        axi.b.resp(RESP_OKAY)
        axi.b.valid(addr_vld & addr_w & mi32.ardy & axi_w_ready_tmp)

        If(mi32.drdy,
           r_data(mi32.drd),
           r_data_vld(1),
        ).Elif(axi.r.ready,
           r_data(None),
           r_data_vld(0),
        )
        axi.r.data(r_data)
        axi.r.resp(RESP_OKAY)
        axi.r.valid(r_data_vld)

        #backpressure(
        #    (r_data_vld & ~axi.r.ready)
        #    | (addr_vld & addr_w & ~axi.b.ready)
        #)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Axi4Lite_to_Mi32()
    print(to_rtl_str(u))
