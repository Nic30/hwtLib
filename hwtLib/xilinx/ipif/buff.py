#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.constants import DIRECTION
from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.xilinx.ipif.hIOIpif import Ipif


class IpifBuff(BusBridge):
    """
    Register or FIFO for IPIF interface, used to break critical paths
    and buffer transactions

    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        Ipif.hwConfig(self)
        self.ADDR_BUFF_DEPTH = HwParam(1)
        self.DATA_BUFF_DEPTH = HwParam(1)

    @override
    def hwDeclr(self):
        if self.ADDR_BUFF_DEPTH != 1 or self.DATA_BUFF_DEPTH != 1:
            raise NotImplementedError()

        with self._hwParamsShared():
            addClkRstn(self)
            self.s = Ipif()
            self.m = Ipif()._m()

    def connectRegistered(self, hwIOFrom: Ipif, hwIOTo: Ipif):
        r = self._reg(hwIOFrom._name + "_reg", hwIOFrom._dtype)
        hwIOFrom._reg = r
        r(hwIOFrom)
        hwIOTo(r)

    @override
    def hwImpl(self):
        din = self.s
        dout = self.m
        for hwIO in din._hwIOs:
            # exclude bus2ip_cs because it needs special care
            if hwIO is din.bus2ip_cs:
                continue

            if hwIO._masterDir == DIRECTION.OUT:
                _din = hwIO
                _dout = getattr(dout, hwIO._name)
            else:
                _dout = hwIO
                _din = getattr(dout, hwIO._name)

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
    from hwt.synth import to_rtl_str
    
    m = IpifBuff()
    print(to_rtl_str(m))
