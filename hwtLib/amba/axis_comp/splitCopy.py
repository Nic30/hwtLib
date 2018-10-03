#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.splitCopy import HsSplitCopy


class AxiSSplitCopy(AxiSCompBase, HsSplitCopy):
    """
    Stream duplicator for AxiStream interfaces
    
    :see: :class:`hwtLib.handshaked.splitCopy.HsSplitCopy`

    .. hwt-schematic::
    """
    pass




if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiSSplitCopy()

    print(toRtl(u))
