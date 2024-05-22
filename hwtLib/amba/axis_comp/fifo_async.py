#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.fifoAsync import HsFifoAsync


@serializeParamsUniq
class Axi4SFifoAsync(Axi4SCompBase, HsFifoAsync):
    """
    Asnchronous fifo for axi-stream interface.

    :see: :class:`hwtLib.handshaked.fifo.HsFifoAsync`

    .. hwt-autodoc:: _example_Axi4SFifoAsync
    """


def _example_Axi4SFifoAsync():

    m = Axi4SFifoAsync()
    m.DEPTH = 5
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4SFifoAsync()

    print(to_rtl_str(m))
