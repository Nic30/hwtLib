#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.axi.axis_compBase import AxiSCompBase
from hwtLib.axi.axis_reg import AxiSReg
from hwtLib.handshaked.reg2 import HandshakedReg2
from hwtLib.interfaces.amba import AxiStream_withoutSTRB


class AxiSReg2(AxiSCompBase, HandshakedReg2):
    """
    Register for axi stream interface
    
    LATENCY=2
    DELAY=1
    """
    regCls = AxiSReg
    pass
    
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSReg2(AxiStream_withoutSTRB)
    
    print(toRtl(u))
