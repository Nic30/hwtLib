#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.axi.axis_compBase import AxiSCompBase
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.axi.axis_reg import AxiSReg


class AxiSFifo(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface. 
    """
    _regCls = AxiSReg
    pass
            
if __name__ == "__main__":
    from hwtLib.interfaces.amba import AxiStream_withoutSTRB
    from hwt.synthesizer.shortcuts import toRtl
    
    u = AxiSFifo(AxiStream_withoutSTRB)
    u.DEPTH.set(4)
    
    print(toRtl(u))    
            
            
            
