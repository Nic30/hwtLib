#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.axi.axis_compBase import AxiSCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.interfaces.amba import AxiStream_withoutSTRB


class AxiSReg(AxiSCompBase, HandshakedReg):
    """
    Register for axi stream interface
    """
    pass
    
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSReg(AxiStream_withoutSTRB)
    
    print(toRtl(u))
