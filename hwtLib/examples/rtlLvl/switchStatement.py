#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def SwitchStatement():
    t = Bits(8)
    n = RtlNetlist()

    In = n.sig("input", t, def_val=8)
    Out = n.sig("output", t)

    Switch(In).add_cases(
        [(i, Out(i + 1)) for i in range(8)]
    )

    interf = {In: DIRECTION.IN, Out: DIRECTION.OUT}
    return n, interf


if __name__ == "__main__":
    netlist, interfaces = SwitchStatement()
    print(netlistToVhdlStr("SwitchStatement", netlist, interfaces))
