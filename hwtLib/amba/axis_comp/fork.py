#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase 
from hwtLib.handshaked.fork import HandshakedFork


class AxiSFork(AxiSCompBase, HandshakedFork):
    pass
            
        
if __name__ == "__main__":
    from hwtLib.amba.axis import AxiStream
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSFork(AxiStream)
    print(toRtl(u))