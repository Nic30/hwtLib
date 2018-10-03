#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.reg import HandshakedReg


class AxiSReg(AxiSCompBase, HandshakedReg):
    """
    Register for AxiStream interfaces
    
    :see: :class:`hwtLib.handshaked.reg.HandshakedReg`
    :note: interface is configurable and schematic is example with AxiStream

    .. hwt-schematic:: _example_AxiSReg
    """
    pass


def _example_AxiSReg():
    u = AxiSReg()
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiSReg()

    print(toRtl(u))
