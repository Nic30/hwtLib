#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.splitCopy import HsSplitCopy


class Axi4SSplitCopy(Axi4SCompBase, HsSplitCopy):
    """
    Stream duplicator for Axi4Stream interfaces

    :see: :class:`hwtLib.handshaked.splitCopy.HsSplitCopy`

    .. hwt-autodoc::
    """
    pass


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = Axi4SSplitCopy()

    print(to_rtl_str(m))
