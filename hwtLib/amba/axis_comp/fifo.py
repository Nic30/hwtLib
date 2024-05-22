#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.fifo import HandshakedFifo


@serializeParamsUniq
class Axi4SFifo(Axi4SCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface.

    :see: :class:`hwtLib.handshaked.fifo.HandshakedFifo`

    .. hwt-autodoc:: _example_Axi4SFifo
    """


def _example_Axi4SFifo():

    m = Axi4SFifo()
    m.DEPTH = 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4SFifo()

    print(to_rtl_str(m))
