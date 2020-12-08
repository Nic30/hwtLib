#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.fifoAsync import HsFifoAsync


@serializeParamsUniq
class AxiSFifoAsync(AxiSCompBase, HsFifoAsync):
    """
    Asnchronous fifo for axi-stream interface.

    :see: :class:`hwtLib.handshaked.fifo.HsFifoAsync`

    .. hwt-autodoc:: _example_AxiSFifoAsync
    """


def _example_AxiSFifoAsync():

    u = AxiSFifoAsync()
    u.DEPTH = 5
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiSFifoAsync()

    print(to_rtl_str(u))
