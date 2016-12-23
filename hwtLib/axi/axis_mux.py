#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.axi.axis_compBase import AxiSCompBase 
from hwtLib.handshaked.mux import HandshakedMux


class AxiSMux(AxiSCompBase, HandshakedMux):
    pass
            

if __name__ == "__main__":
    from hwtLib.interfaces.amba import AxiStream
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSMux(AxiStream)
    print(toRtl(u))