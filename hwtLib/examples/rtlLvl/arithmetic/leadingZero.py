#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def LeadingZero():
    t = Bits(64)
    resT = Bits(8)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    index = n.sig("s_indexOfFirstZero", resT)

    leadingZeroTop = None  # index is index of first empty record or last one
    for i in reversed(range(8)):
        connections = index(i)
        if leadingZeroTop is None:
            leadingZeroTop = connections 
        else:
            leadingZeroTop = If(s_in[i]._eq(0),
               connections
            ).Else(
               leadingZeroTop
            )

    interf = {s_in: DIRECTION.IN, index: DIRECTION.OUT}

    return n, interf


if __name__ == "__main__":
    netlist, interfaces = LeadingZero()
    print(netlistToVhdlStr("LeadingZero", netlist, interfaces))
