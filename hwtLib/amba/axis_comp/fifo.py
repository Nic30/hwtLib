#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.fifo import HandshakedFifo


@serializeParamsUniq
class AxiSFifo(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface.

    :see: :class:`hwtLib.handshaked.fifo.HandshakedFifo`

    .. hwt-autodoc:: _example_AxiSFifo
    """


def _example_AxiSFifo():

    u = AxiSFifo()
    u.DEPTH = 4
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiSFifo()

    print(to_rtl_str(u))
