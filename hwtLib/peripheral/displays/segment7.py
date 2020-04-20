#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.unit import Unit
from hwt.interfaces.std import VectSignal
from hwt.code import Switch


class Segment7(Unit):
    """
    7-segment display decoder

    :note: led in display becomes active when output = 0

    Display pin connection on image below.

    .. code-block:: raw

        -------------
        |     0     |
        -------------
        | 5 |   | 1 |
        -------------
        |     6     |
        -------------
        | 4 |   | 2 |
        -------------
        |     3     |
        -------------

    .. hwt-schematic::
    """

    def _declr(self):
        self.dataIn = VectSignal(4)
        self.dataOut = VectSignal(7)._m()

    def _impl(self):
        dec = [
            # 0
            0b0000001,
            # 1
            0b1001111,
            # 2
            0b0010010,
            # 3
            0b0000110,
            # 4
            0b1001100,
            # 5
            0b0100100,
            # 6
            0b0100000,
            # 7
            0b0001111,
            # 8
            0b0000000,
            # 9
            0b0000100,

        ]
        Switch(self.dataIn) \
        .addCases(enumerate([self.dataOut(v) for v in dec])) \
        .Default(
           # display off when value is out of range
           self.dataOut(0b1111111)
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(Segment7()))
