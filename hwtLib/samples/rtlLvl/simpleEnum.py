#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.serializer.vhdlFormater import formatVhdl
from hwt.code import If
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


if __name__ == "__main__":
    t = vecT(8)
    fsmT = Enum('fsmT', ['send0', 'send1'])
    
    n = RtlNetlist()
    
    s_out = n.sig("s_out", t)
    s_in0 = n.sig("s_in0", t)
    s_in1 = n.sig("s_in1", t)    
    clk = n.sig("clk")
    syncRst = n.sig("rst")
    
    
    fsmSt = n.sig("fsmSt", fsmT, clk, syncRst, fsmT.send0)
    If(fsmSt._eq(fsmT.send0),
        s_out ** s_in0,
        fsmSt ** fsmT.send1,
    ).Else(
        s_out ** s_in1 ,
        fsmSt ** fsmT.send0
    )
    
    interf = [clk, syncRst, s_in0, s_in1, s_out]
    
    for o in n.synthesize("SimpleEnum", interf):
            print(formatVhdl(str(o)))

    
