#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.amba.axis_comp.reg import AxiSReg


class AxiSFifo(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface.

    .. aafig::
                 +-+-+-+-+-+
         input   | | | | | | output
       +-stream--> | | | | +-stream->
                 | | | | | |
                 +-+-+-+-+-+
    """
    _regCls = AxiSReg


if __name__ == "__main__":
    from hwtLib.amba.axis import AxiStream_withoutSTRB
    from hwt.synthesizer.utils import toRtl

    u = AxiSFifo(AxiStream_withoutSTRB)
    u.DEPTH.set(4)

    print(toRtl(u))
