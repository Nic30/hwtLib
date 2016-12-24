#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.serializer.vhdlFormater import formatVhdl
from hwt.code import Switch
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


if __name__ == "__main__":
    t = vecT(8)
    n = RtlNetlist()
    
    In = n.sig("input", t, defVal=8)
    Out = n.sig("output", t)
    
    Switch(In).addCases(
        [(i, Out ** (i + 1)) for i in range(8)]
    )
    
    
    interf = [In, Out]
    
    for o in n.synthesize("SwitchStatement", interf):
            print(formatVhdl(str(o)))
