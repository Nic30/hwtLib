#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.examples.simpleHwModule import SimpleHwModule

if __name__ == "__main__":  # alias python main function
    from hwt.serializer.vhdl import Vhdl2008Serializer
    from hwt.serializer.ip_packager import IpPackager
    from os.path import expanduser

    # create instance of :class:`hwt.hwModule.HwModule` (unit is like verilog module)
    m = SimpleHwModule()
    # create instace of IpPackager and configure it
    # if name is not specified name will be name of :class:`hwt.hwModule.HwModule` class
    p = IpPackager(m, serializer_cls=Vhdl2008Serializer)
    # generate IP-core package
    p.createPackage(expanduser("~/Documents/ip_repo"))
