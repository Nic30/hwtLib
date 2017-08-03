#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, connect
from hwtLib.handshaked.splitCopy import HsSplitCopy


class HsSplitPrioritized(HsSplitCopy):
    """
    Split input stream to n output streams
    Data is send to output interface which is ready and has lowest index

    combinational

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
    """
    def _declr(self):
        HsSplitCopy._declr(self)

    def _impl(self):
        dataOut = list(reversed(self.dataOut))
        self.getRd(self.dataIn) ** Or(*map(lambda x: self.getRd(x), dataOut))
        for i, out in enumerate(dataOut):
            allWitLowerPriority = dataOut[i+1:]
            vld = self.getVld(self.dataIn)
            for _vld in map(lambda x: ~self.getRd(x), allWitLowerPriority):
                vld = vld & _vld

            connect(self.dataIn, out, exclude={self.getRd(out), self.getVld(out)})
            self.getVld(out) ** vld


if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HsSplitPrioritized(Handshaked)
    u.OUTPUTS.set(4)
    print(toRtl(u))
