#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And
from hwt.interfaces.std import Handshaked
from hwt.synthesizer.param import Param
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwt.synthesizer.hObjList import HObjList


class HsSplitCopy(HandshakedCompBase):
    """
    Clone input stream to n identical output streams
    transaction is made in all interfaces or none of them

    :note: combinational

    .. aafig::
                                     +---------+
                              +------> clone0  |
                              |      +---------+
                      +-------+
         input stream |       |      +---------+
        +-------------> copy  +------> clone1  |
                      |       |      +---------+
                      +-------+
                              |      +---------+
                              +------> clone2  |
                                     +---------+
    
    .. hwt-schematic:: _example_HsSplitCopy
    
    """
    def _config(self):
        self.OUTPUTS = Param(2)
        super()._config()

    def _declr(self):
        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = HObjList(
                self.intfCls()._m() for _ in range(int(self.OUTPUTS))
            )

    def _impl(self):
        rd = self.get_ready_signal
        vld = self.get_valid_signal
        data = self.get_data

        for io in self.dataOut:
            for i, o in zip(data(self.dataIn), data(io)):
                o(i)

        outRd = And(*[rd(i) for i in self.dataOut])
        rd(self.dataIn)(outRd)

        for o in self.dataOut:
            # everyone else is ready and input is valid
            deps = [vld(self.dataIn)]
            for otherO in self.dataOut:
                if otherO is o:
                    continue
                deps.append(rd(otherO))
            _vld = And(*deps)

            vld(o)(_vld)


def _example_HsSplitCopy():
    u = HsSplitCopy(Handshaked)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsSplitCopy()
    print(toRtl(u))
