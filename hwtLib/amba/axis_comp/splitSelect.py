#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.splitSelect import HsSplitSelect


class AxiSSpliSelect(AxiSCompBase, HsSplitSelect):
    """
    Send input frame to one of N output streams as specified by selectOneHot interface

    :see: :class:`hwtLib.handshaked.splitSelect.HsSplitSelect`

    .. hwt-schematic:: _example_AxiSSpliSelect
    """

    def _select_consume_en(self):
        return self.dataIn.last


def _example_AxiSSpliSelect():
    from hwtLib.amba.axis import AxiStream
    u = AxiSSpliSelect(AxiStream)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiSSpliSelect()
    print(toRtl(u))
