#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit


class SimpleUnit(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()._m()

    def _impl(self):
        self.b(self.a)


if __name__ == "__main__":  # alias python main function
    from hwt.serializer.vhdl.serializer import VhdlSerializer
    from hwt.serializer.ip_packager import IpPackager
    from os.path import expanduser

    # create instance of Unit (unit is like verilog module)
    u = SimpleUnit()
    # create instace of IpPackager and configure it
    # if name is not specified name will be name of Unit class
    p = IpPackager(u, serializer=VhdlSerializer)
    # generate IP-core package
    p.createPackage(expanduser("~/Documents/ip_repo"))