#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwt.serializer.ipCoreWrapper import IpCoreWrapper
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream


class ArrayIntfExample(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = AxiStream(asArraySize=2)

    def _impl(self):
        for intf in self.a:
            intf.ready(1)


if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it
    # only when this script is running as main
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = IpCoreWrapper(ArrayIntfExample())
    print(toRtl(u))
