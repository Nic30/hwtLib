#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis import AxiStream_withoutSTRB
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwtLib.handshaked.reg2 import HandshakedReg2


class AxiSReg2(AxiSCompBase, HandshakedReg2):
    """
    Register for axi stream interface
    
    LATENCY=2
    DELAY=1
    """
    regCls = AxiSReg
    
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSReg2(AxiStream_withoutSTRB)
    
    print(toRtl(u))
