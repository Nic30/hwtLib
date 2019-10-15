#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.amba.axis_comp.reg import AxiSReg


class AxiSFifo(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface.

    :see: :class:`hwtLib.handshaked.fifo.HandshakedFifo`

    .. hwt-schematic:: _example_AxiSFifo
    """
    _regCls = AxiSReg


def _example_AxiSFifo():

    u = AxiSFifo()
    u.DEPTH = 4
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiSFifo()

    print(toRtl(u))
