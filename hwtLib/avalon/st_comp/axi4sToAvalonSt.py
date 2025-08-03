#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.avalon.st import AvalonST
from hwtLib.logic.countLeading import CountTrailingZeros


class Axi4Stream_to_AvalonST(HwModule):
    """
    :note: expect user signal to be Concat(error, sof)
    
    .. hwt-autodoc:: _example_Axi4Stream_to_AvalonST
    """

    @override
    def hwConfig(self) -> None:
        Axi4Stream.hwConfig(self)

    @override
    def hwDeclr(self) -> None:
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = Axi4Stream()
            self.dataOut: AvalonST = AvalonST()._m()
            m = self.dataOut
            assert m.dataBitsPerSymbol == 8, self.dataBitsPerSymbol
            if self.ID_WIDTH:
                m.maxChannel = int(2 ** self.ID_WIDTH)
            assert m.readyLatency == 0, m.readyLatency
            assert not m.readyAllowance, m.readyAllowance
            if self.USER_WIDTH > 1:
                m.ERROR_WIDTH = self.USER_WIDTH - 1
            m.USE_EMPTY = self.USE_KEEP or self.USE_STRB
            assert m.packetsPerClock == 1, m.packetsPerClock

    @override
    def hwImpl(self) -> None:
        s: Axi4Stream = self.dataIn
        m: AvalonST = self.dataOut
        if self.ID_WIDTH:
            m.channel(s.id)

        if m.USE_EMPTY:
            if self.USE_KEEP and self.USE_STRB:
                keep = s.keep & s.strb
            elif self.USE_KEEP:
                keep = s.keep
            else:
                assert self.USE_STRB
                keep = s.strb
            cttz = CountTrailingZeros()
            cttz.DATA_WIDTH = keep._dtype.bit_length()
            self.cttz = cttz
            cttz.data_in(keep)
            m.empty(cttz.data_out._trunc(m.empty._dtype.bit_length())) # cttz coputes also the number for keep==0

        m.vld(s.valid)
        s.ready(m.rd)
        m.data(s.data)
        m.endOfPacket(s.last)
        m.startOfPacket(s.user[0])
        if self.USER_WIDTH > 1:
            m.error(s.user[:1])


def _example_Axi4Stream_to_AvalonST():
    m = Axi4Stream_to_AvalonST()
    m.USE_STRB = True
    m.USE_KEEP = True
    m.ID_WIDTH = 4
    m.USER_WIDTH = 1 + 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4Stream_to_AvalonST()
    print(to_rtl_str(m))
