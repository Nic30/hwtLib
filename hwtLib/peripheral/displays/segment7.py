#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class Segment7(HwModule):
    """
    7-segment display decoder

    :note: led in display becomes active when output = 0

    Display pin connection on image below.

    .. code-block:: text

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

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.dataIn = HwIOVectSignal(4)
        self.dataOut = HwIOVectSignal(7)._m()

    @override
    def hwImpl(self):
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
        .add_cases(enumerate([self.dataOut(v) for v in dec])) \
        .Default(
           # display off when value is out of range
           self.dataOut(0b1111111)
        )


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(Segment7()))
