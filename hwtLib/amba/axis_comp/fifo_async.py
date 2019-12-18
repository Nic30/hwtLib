#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwtLib.handshaked.fifoAsync import HsFifoAsync


class AxiSFifoAsync(AxiSCompBase, HsFifoAsync):
    """
    Asnchronous fifo for axi-stream interface.

    :see: :class:`hwtLib.handshaked.fifo.HsFifoAsync`

    .. hwt-schematic:: _example_AxiSFifoAsync
    """
    _regCls = AxiSReg


def _example_AxiSFifoAsync():

    u = AxiSFifoAsync()
    u.DEPTH = 5
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiSFifoAsync()

    print(toRtl(u))
