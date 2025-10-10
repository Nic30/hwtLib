#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.handshaked.compBase import HandshakedCompBase


class HsSplitCopy(HandshakedCompBase):
    """
    Clone input stream to n identical output streams
    transaction is made in all interfaces or none of them

    :note: combinational

    .. figure:: ./_static/HsSplitCopy.png

    .. hwt-autodoc:: _example_HsSplitCopy
    """

    @override
    def hwConfig(self):
        self.OUTPUTS = HwParam(2)
        super().hwConfig()

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            self.dataIn = self.hwIOCls()
            self.dataOut = HwIOArray(
                self.hwIOCls() for _ in range(int(self.OUTPUTS))
            )._m()

    @override
    def hwImpl(self):
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
    m = HsSplitCopy(HwIODataRdVld)
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HsSplitCopy()
    print(to_rtl_str(m))
