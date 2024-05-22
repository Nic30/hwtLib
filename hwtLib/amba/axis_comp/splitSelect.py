#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.splitSelect import HsSplitSelect


class Axi4SSpliSelect(Axi4SCompBase, HsSplitSelect):
    """
    Send input frame to one of N output streams as specified
    by selectOneHot interface

    :see: :class:`hwtLib.handshaked.splitSelect.HsSplitSelect`

    .. hwt-autodoc::
    """

    def _select_consume_en(self):
        return self.dataIn.last


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = Axi4SSpliSelect()
    print(to_rtl_str(m))
