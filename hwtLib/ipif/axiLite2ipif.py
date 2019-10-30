#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch, If, FsmBuilder
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.utils import addClkRstn

from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.constants import RESP_SLVERR, RESP_OKAY
from hwtLib.ipif.intf import Ipif
from hwtLib.abstract.busBridge import BusBridge


class AxiLite2Ipif(BusBridge):
    """
    Bridge from AxiLite interface to IPIF interface

    .. hwt-schematic::
    """

    def _config(self) -> None:
        Ipif._config(self)

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = Axi4Lite()
            self.m = Ipif()._m()

    def handleResp(self):
        ipif = self.m
        axi = self.s
        resp = self._sig("resp", axi.r.resp._dtype)
        respTmp = self._sig("respTmp", resp._dtype)
        respReg = self._reg("respReg", resp._dtype)

        If(ipif.ip2bus_error,
           resp(RESP_SLVERR)
        ).Else(
           resp(RESP_OKAY)
        )
        If(ipif.ip2bus_wrack | ipif.ip2bus_rdack,
           respReg(resp),
           respTmp(resp)
        ).Else(
           respTmp(respReg)
        )

        axi.r.resp(respTmp)
        axi.b.resp(respTmp)

    def handleAddr(self, st):
        st_t = st._dtype
        ipif = self.m
        axi = self.s

        addr = self._reg("addr", axi.aw.addr._dtype)
        If(st._eq(st_t.idle),
            If(axi.ar.valid,
                addr(axi.ar.addr)
            ).Elif(axi.aw.valid,
                addr(axi.aw.addr)
            )
        )
        ipif.bus2ip_addr(addr)

    def mainFsm(self, dataRegR_vld):
        ipif = self.m
        axi = self.s
        st_t = HEnum("st_t", [
            "idle",
            "write", "write_wait_data", "write_ack",
            "read", "read_ack"
        ])

        st = FsmBuilder(self, st_t
        ).Trans(st_t.idle,
                # ready for new request
                (axi.ar.valid, st_t.read),
                (axi.aw.valid, st_t.write_wait_data),
        ).Trans(st_t.write_wait_data,
                # has address but needs data from axi
                (axi.w.valid, st_t.write),
        ).Trans(st_t.write,
                # has address and data from axi and writing to ipif
                (ipif.ip2bus_wrack & axi.b.ready, st_t.idle),
                (ipif.ip2bus_wrack, st_t.write_ack),
        ).Trans(st_t.write_ack,
                # data was writen waiting for write response to axi,
                (axi.b.ready, st_t.idle)
        ).Trans(st_t.read,
                # has address, reading from ipif
                ((ipif.ip2bus_rdack | dataRegR_vld) & axi.r.ready, st_t.idle),
                (ipif.ip2bus_rdack, st_t.read_ack),
        ).Trans(st_t.read_ack,
                # read from ipif complete, waiting for axi to accept data
                (axi.r.ready, st_t.idle)
        ).stateReg

        return st

    def _impl(self) -> None:
        ipif = self.m
        axi = self.s
        r = self._reg

        dataRegR_vld = r("dataRegR_vld", def_val=0)
        st = self.mainFsm(dataRegR_vld)
        st_t = st._dtype
        self.handleResp()
        self.handleAddr(st)

        idle = st._eq(st_t.idle)
        axi.ar.ready(idle)
        axi.aw.ready(idle & ~axi.ar.valid)
        axi.w.ready(st._eq(st_t.write_wait_data))

        dataRegR = r("dataR", axi.r.data._dtype)
        dataRegW = r("dataW", axi.w.data._dtype)
        strbRegW = r("strbW", axi.w.strb._dtype)

        If(((st._eq(st_t.idle) & axi.aw.valid & ~axi.ar.valid)
             | st._eq(st_t.write_wait_data)) & axi.w.valid,
            dataRegW(axi.w.data),
            strbRegW(axi.w.strb)
        )
        If(ipif.ip2bus_rdack & (
            (idle & axi.ar.valid) | st._eq(st_t.read)),
            dataRegR(ipif.ip2bus_data),
        )

        If(idle,
           dataRegR_vld(ipif.ip2bus_rdack),
        )

        If(idle,
           ipif.bus2ip_be(axi.w.strb)
        ).Else(
           ipif.bus2ip_be(strbRegW)
        )

        Switch(st)\
        .Case(st_t.read,
              If(dataRegR_vld,
                 axi.r.data(dataRegR),
                 axi.r.valid(1)
              ).Else(
                 axi.r.data(ipif.ip2bus_data),
                 axi.r.valid(ipif.ip2bus_rdack)
              )
        ).Case(st_t.read_ack,
              axi.r.data(dataRegR),
              axi.r.valid(1),
        ).Default(
            axi.r.data(None),
            axi.r.valid(0)
        )

        Switch(st)\
        .Case(st_t.write,
            axi.b.valid(ipif.ip2bus_wrack)
        ).Case(st_t.write_ack,
            axi.b.valid(1)
        ).Default(
            axi.b.valid(0)
        )

        ipif.bus2ip_data(dataRegW)
        ipif.bus2ip_cs(st._eq(st_t.write) | st._eq(st_t.read))
        ipif.bus2ip_rnw(st._eq(st_t.read))


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiLite2Ipif()
    print(toRtl(u))
