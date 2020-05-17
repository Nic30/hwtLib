#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def SimpleEnum():
    t = Bits(8)
    fsmT = HEnum('fsmT', ['send0', 'send1'])

    n = RtlNetlist()

    s_out = n.sig("s_out", t)
    s_in0 = n.sig("s_in0", t)
    s_in1 = n.sig("s_in1", t)
    clk = n.sig("clk")
    syncRst = n.sig("rst")

    fsmSt = n.sig("fsmSt", fsmT, clk, syncRst, fsmT.send0)
    If(fsmSt._eq(fsmT.send0),
        s_out(s_in0),
        fsmSt(fsmT.send1),
    ).Else(
        s_out(s_in1),
        fsmSt(fsmT.send0)
    )

    interf = {clk: DIRECTION.IN, syncRst: DIRECTION.IN,
              s_in0: DIRECTION.IN, s_in1: DIRECTION.IN,
              s_out: DIRECTION.OUT}
    return n, interf


if __name__ == "__main__":
    netlist, interfaces = SimpleEnum()
    print(netlistToVhdlStr("SimpleEnum", netlist, interfaces))
