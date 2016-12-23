#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.axi.axis_compBase import AxiSCompBase 
from hwtLib.handshaked.fork import HandshakedFork


class AxiSFork(AxiSCompBase, HandshakedFork):
    pass
            
        
if __name__ == "__main__":
    from hwtLib.interfaces.amba import AxiStream
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSFork(AxiStream)
    print(toRtl(u))