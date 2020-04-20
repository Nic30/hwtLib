#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def SimpleWhile():
    t = Bits(8)
    n = RtlNetlist()

    boundary = n.sig("boundary", t, def_val=8)
    s_out = n.sig("s_out", t)

    start = n.sig("start")
    en = n.sig("en")

    clk = n.sig("clk")
    syncRst = n.sig("rst")

    counter = n.sig("counter", t, clk, syncRst, 0)
    If(start,
        counter(boundary)
    ).Elif(en,
        counter(counter - 1)
    )

    s_out(counter)

    interf = {clk: DIRECTION.IN, syncRst: DIRECTION.IN,
              start: DIRECTION.IN, en: DIRECTION.IN,
              s_out: DIRECTION.OUT}
    return n, interf


if __name__ == "__main__":
    netlist, interfaces = SimpleWhile()
    print(netlistToVhdlStr("SimpleWhile", netlist, interfaces))
