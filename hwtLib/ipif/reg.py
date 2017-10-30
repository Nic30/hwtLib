#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.ipif.intf import Ipif


class IpifReg(Unit):
    def _config(self):
        Ipif._config(self)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.dataIn = Ipif()
            self.dataOut = Ipif()

    def connectRegistered(self, intfFrom, intfTo):
        r = self._reg(intfFrom._name + "_reg", intfFrom._dtype)
        intfFrom._reg = r
        r(intfFrom)
        intfTo(r)

    def _impl(self):
        din = self.dataIn
        dout = self.dataOut
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

        cs = self._reg("bus2ip_cs_reg", defVal=0)

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
    from hwt.synthesizer.utils import toRtl
    u = IpifReg()

    print(toRtl(u))

