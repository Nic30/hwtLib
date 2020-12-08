#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.cdc import HandshakedCdc


@serializeParamsUniq
class AxiSCdc(AxiSCompBase, HandshakedCdc):
    """
    CDC (Clock domain crossing) for axi-stream like interfaces

    :see: :class:`hwtLib.handshaked.cdc.HandshakedCdc`

    .. hwt-autodoc:: example_AxiSCdc
    """


def example_AxiSCdc():
    u = AxiSCdc()
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = example_AxiSCdc()

    print(to_rtl_str(u))
