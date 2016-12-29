#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.types.enum import Enum
from hwt.serializer.vhdlFormater import formatVhdl
from hwt.code import If
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


def axiReaderCore():
    n = RtlNetlist()
    rSt_t = Enum('rSt_t', ['rdIdle', 'rdData'])
    
    rSt = n.sig('rSt', rSt_t)
    arRd = n.sig('arRd')
    arVld = n.sig('arVld')
    rVld = n.sig('rVld')
    rRd = n.sig('rRd')

    # ar fsm next
    If(arRd,
       # rdIdle
        If(arVld,
           rSt ** rSt_t.rdData 
        ).Else(
           rSt ** rSt_t.rdIdle
        )
    ).Else(
        # rdData
        If(rRd & rVld,
           rSt ** rSt_t.rdIdle
        ).Else(
           rSt ** rSt_t.rdData 
        )
    )
    
    return n, [rSt, arRd, arVld, rVld, rRd]
    
if __name__ == "__main__":
    n, interf = axiReaderCore()
    
    for o in n.synthesize("AxiReaderCore", interf):
            print(formatVhdl(str(o)))
