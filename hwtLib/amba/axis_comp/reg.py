#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.reg import HandshakedReg


class Axi4SReg(Axi4SCompBase, HandshakedReg):
    """
    Register for Axi4Stream interfaces

    :see: :class:`hwtLib.handshaked.reg.HandshakedReg`
    :note: interface is configurable and schematic is example with Axi4Stream

    .. hwt-autodoc:: _example_Axi4SReg
    """
    pass


def _example_Axi4SReg():
    m = Axi4SReg()
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = _example_Axi4SReg()
    print(to_rtl_str(m))
