#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.splitSelect import HsSplitSelect


class AxiSSpliSelect(AxiSCompBase, HsSplitSelect):
    pass


if __name__ == "__main__":
    from hwtLib.amba.axis import AxiStream
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSSpliSelect(AxiStream)
    print(toRtl(u))
