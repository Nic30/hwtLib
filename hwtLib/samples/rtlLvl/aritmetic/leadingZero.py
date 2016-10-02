#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.serializer.vhdlFormater import formatVhdl
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.rtlLevel.netlist import RtlNetlist


def LeadingZero():
    t = vecT(64)
    resT = vecT(8)
    n = RtlNetlist()
    
    s_in = n.sig("s_in", t)
    index = n.sig("s_indexOfFirstZero", resT)
    
    leadingZeroTop = None  # index is index of first empty record or last one
    for i in reversed(range(8)):
        connections = index ** i
        if leadingZeroTop is None:
            leadingZeroTop = connections 
        else:
            leadingZeroTop = If(s_in[i]._eq(0),
               connections
            ).Else(
               leadingZeroTop
            )    
    
    interf = [s_in, index]
    
    return n, interf

if __name__ == "__main__":
    n, interf = LeadingZero()
    
    for o in n.synthesize("LeadingZero", interf):
            print(formatVhdl(str(o)))

