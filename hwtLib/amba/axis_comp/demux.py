#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase 
from hwtLib.handshaked.demux import HandshakedDemux


class AxiSDemux(AxiSCompBase, HandshakedDemux):
    pass
            

if __name__ == "__main__":
    from hwtLib.amba.axis import AxiStream
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSDemux(AxiStream)
    print(toRtl(u))