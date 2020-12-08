#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.splitCopy import HsSplitCopy


class AxiSSplitCopy(AxiSCompBase, HsSplitCopy):
    """
    Stream duplicator for AxiStream interfaces

    :see: :class:`hwtLib.handshaked.splitCopy.HsSplitCopy`

    .. hwt-autodoc::
    """
    pass


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AxiSSplitCopy()

    print(to_rtl_str(u))
