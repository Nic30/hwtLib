#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.cdc import HandshakedCdc


@serializeParamsUniq
class Axi4SCdc(Axi4SCompBase, HandshakedCdc):
    """
    CDC (Clock domain crossing) for axi-stream like interfaces

    :see: :class:`hwtLib.handshaked.cdc.HandshakedCdc`

    .. hwt-autodoc:: example_Axi4SCdc
    """


def example_Axi4SCdc():
    m = Axi4SCdc()
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = example_Axi4SCdc()

    print(to_rtl_str(m))
