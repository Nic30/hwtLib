#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.reg import HandshakedReg


class AxiSReg(AxiSCompBase, HandshakedReg):
    """
    Register for axi stream interface
    """
    pass
    
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.amba.axis import AxiStream_withoutSTRB
    u = AxiSReg(AxiStream_withoutSTRB)
    
    print(toRtl(u))
