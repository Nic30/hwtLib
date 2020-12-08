#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.xilinx.ipif.intf import Ipif


class IpifBuff(BusBridge):
    """
    Register or fifo for IPIF interface, used to break critical paths
    and buffer transactions

    .. hwt-autodoc::
    """
    def _config(self):
        Ipif._config(self)
        self.ADDR_BUFF_DEPTH = Param(1)
        self.DATA_BUFF_DEPTH = Param(1)

    def _declr(self):
        if self.ADDR_BUFF_DEPTH != 1 or self.DATA_BUFF_DEPTH != 1:
            raise NotImplementedError()

        with self._paramsShared():
            addClkRstn(self)
            self.s = Ipif()
            self.m = Ipif()._m()

    def connectRegistered(self, intfFrom, intfTo):
        r = self._reg(intfFrom._name + "_reg", intfFrom._dtype)
        intfFrom._reg = r
        r(intfFrom)
        intfTo(r)

    def _impl(self):
        din = self.s
        dout = self.m
        for i in din._interfaces:
            # exclude bus2ip_cs because it needs special care
            if i is din.bus2ip_cs:
                continue

            if i._masterDir == DIRECTION.OUT:
                _din = i
                _dout = getattr(dout, i._name)
            else:
                _dout = i
                _din = getattr(dout, i._name)

            self.connectRegistered(_din, _dout)

        cs = self._reg("bus2ip_cs_reg", def_val=0)

        # now bus2ip_cs has to be set after addr etc are valid
        # but we must not let start another transaction directly after one ended
        If(dout.ip2bus_rdack._reg | dout.ip2bus_wrack._reg,
            cs(0),
            dout.bus2ip_cs(0)
        ).Else(
            cs(din.bus2ip_cs),
            dout.bus2ip_cs(cs)
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = IpifBuff()

    print(to_rtl_str(u))
