#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.avalon.st import AvalonST
from pyMathBitPrecise.bit_utils import mask


class AvalonST_to_Axi4Stream(HwModule):
    """
    
    .. hwt-autodoc:: _example_AvalonST_to_Axi4Stream
    """

    @override
    def hwConfig(self) -> None:
        AvalonST.hwConfig(self)

    @override
    def hwDeclr(self) -> None:
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = AvalonST()
            self.dataOut: Axi4Stream = Axi4Stream()._m()
            assert self.dataBitsPerSymbol == 8, self.dataBitsPerSymbol
            if self.maxChannel:
                self.dataOut.ID_WIDTH = log2ceil(self.maxChannel)
            assert self.readyLatency == 0, self.readyLatency
            assert not self.readyAllowance, self.readyAllowance
            m = self.dataOut
            m.USER_WIDTH = 1 + self.ERROR_WIDTH  # 1 for startOfPacket
            m.USE_KEEP = self.USE_EMPTY
            assert self.packetsPerClock == 1, self.packetsPerClock

    @override
    def hwImpl(self) -> None:
        m: Axi4Stream = self.dataOut
        s: AvalonST = self.dataIn
        if self.maxChannel:
            m.id(s.channel)
        if self.USE_EMPTY:
            size = m.keep._dtype.bit_length()
            emptyToMaskROM = [mask(size - empty) for empty in range(s.empty._dtype.domain_size())]
            emptyToMaskROM = self._sig("emptyToMaskROM", m.keep._dtype[len(emptyToMaskROM)], emptyToMaskROM)
            m.keep(emptyToMaskROM[s.empty])

        m.valid(s.vld)
        s.rd(m.ready)
        m.data(s.data)
        m.last(s.endOfPacket)
        user = s.startOfPacket
        if self.ERROR_WIDTH:
            user = Concat(s.error, user)
        m.user(user)


def _example_AvalonST_to_Axi4Stream():
    m = AvalonST_to_Axi4Stream()
    m.USE_EMPTY = True
    m.maxChannel = 2
    m.ERROR_WIDTH = 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_AvalonST_to_Axi4Stream()
    print(to_rtl_str(m))
