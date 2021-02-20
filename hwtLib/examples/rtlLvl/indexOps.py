#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from hwt.hdl.types.bits import Bits
from ipCorePackager.constants import DIRECTION


def IndexOps():
    t = Bits(8)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    s_out = n.sig("s_out", t)

    s_in2 = n.sig("s_in2", t)
    s_out2 = n.sig("s_out2", t)

    s_in3 = n.sig("s_in3", Bits(16))
    s_out3 = n.sig("s_out3", t)

    s_in4a = n.sig("s_in4a", t)
    s_in4b = n.sig("s_in4b", t)

    s_out4 = n.sig("s_out4", Bits(16))

    s_out(s_in[4:]._concat(Bits(4).from_py(2)))

    s_out2[4:](s_in2[4:])
    s_out2[:4](s_in2[:4])

    s_out3(s_in3[8:])

    s_out4[8:](s_in4a)
    s_out4[(8 + 8):8](s_in4b)

    interf = {
        s_in: DIRECTION.IN,
        s_out: DIRECTION.OUT,
        s_in2: DIRECTION.IN,
        s_out2: DIRECTION.OUT,
        s_in3: DIRECTION.IN,
        s_out3: DIRECTION.OUT,
        s_in4a: DIRECTION.IN,
        s_in4b: DIRECTION.IN,
        s_out4: DIRECTION.OUT
    }

    return n, interf


if __name__ == "__main__":
    netlist, interfaces = IndexOps()
    print(netlistToVhdlStr("IndexOps", netlist, interfaces))