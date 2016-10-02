#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.axi.axis_compBase import AxiSCompBase
from hwtLib.handshaked.fifo import HandshakedFifo


class AxiSFifo(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface. 
    """
    pass
            
if __name__ == "__main__":
    from hwtLib.interfaces.amba import AxiStream_withoutSTRB
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    
    u = AxiSFifo(AxiStream_withoutSTRB)
    u.DEPTH.set(4)
    
    print(toRtl(u))    
            
            
            
