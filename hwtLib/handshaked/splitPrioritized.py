#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or
from hwtLib.handshaked.splitCopy import HsSplitCopy


class HsSplitPrioritized(HsSplitCopy):
    """
    Split input stream to N output streams.
    Data is send to output interface which is ready and has lowest index.

    :note: combinational

    .. figure:: ./_static/HsSplitPrioritized.png

    .. hwt-autodoc:: _example_HsSplitPrioritized
    """

    def _declr(self):
        HsSplitCopy._declr(self)

    def _impl(self):
        dataOut = list(reversed(self.dataOut))
        self.get_ready_signal(self.dataIn)(Or(*map(lambda x: self.get_ready_signal(x), dataOut)))
        for i, out in enumerate(dataOut):
            allWitLowerPriority = dataOut[i + 1:]
            vld = self.get_valid_signal(self.dataIn)
            for _vld in map(lambda x:~self.get_ready_signal(x), allWitLowerPriority):
                vld = vld & _vld

            out(self.dataIn,
                exclude={self.get_ready_signal(out), self.get_valid_signal(out)})
            self.get_valid_signal(out)(vld)


def _example_HsSplitPrioritized():
    from hwt.hwIOs.std import HwIODataRdVld

    m = HsSplitPrioritized(HwIODataRdVld)
    m.OUTPUTS = 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HsSplitPrioritized()
    print(to_rtl_str(m))
