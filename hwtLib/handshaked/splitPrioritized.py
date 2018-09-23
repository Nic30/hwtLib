#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, connect
from hwtLib.handshaked.splitCopy import HsSplitCopy


class HsSplitPrioritized(HsSplitCopy):
    """
    Split input stream to N output streams.
    Data is send to output interface which is ready and has lowest index.

    :note: combinational

    .. aafig::
                                     +-------+
                              +------> out0  |
                              |      +-------+
                      +-------+
         input stream |       |      +-------+
        +-------------> split +------> out1  |
                      |       |      +-------+
                      +-------+
                              |      +-------+
                              +------> out2  |
                                     +-------+
    
    .. hwt-schematic:: _example_HsSplitPrioritized
                                
    """
    def _declr(self):
        HsSplitCopy._declr(self)

    def _impl(self):
        dataOut = list(reversed(self.dataOut))
        self.getRd(self.dataIn)(Or(*map(lambda x: self.getRd(x), dataOut)))
        for i, out in enumerate(dataOut):
            allWitLowerPriority = dataOut[i+1:]
            vld = self.getVld(self.dataIn)
            for _vld in map(lambda x: ~self.getRd(x), allWitLowerPriority):
                vld = vld & _vld

            connect(self.dataIn, out, exclude={self.getRd(out), self.getVld(out)})
            self.getVld(out)(vld)


def _example_HsSplitPrioritized():
    from hwt.interfaces.std import Handshaked
    u = HsSplitPrioritized(Handshaked)
    u.OUTPUTS.set(4)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsSplitPrioritized()
    print(toRtl(u))
