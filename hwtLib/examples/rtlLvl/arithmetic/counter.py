#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from ipCorePackager.constants import DIRECTION


def Counter():
    t = Bits(8)
    n = RtlNetlist("LeadingZero")

    en = n.sig("en")
    rst = n.sig("rst")
    clk = n.sig("clk")
    s_out = n.sig("s_out", t)
    cnt = n.sig("cnt", t, clk=clk, syncRst=rst, def_val=0)

    If(en,
       cnt(cnt + 1)
    )

    s_out(cnt)

    interf = {rst: DIRECTION.IN, clk: DIRECTION.IN,
              s_out: DIRECTION.OUT, en: DIRECTION.IN}

    return n, interf


if __name__ == "__main__":
    netlist, interfaces = Counter()
    print(netlistToVhdlStr("Counter", netlist, interfaces))
