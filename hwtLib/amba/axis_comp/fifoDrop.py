#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, Optional, Union

from hwt.hwIOs.std import HwIOSignal, HwIORst_n, HwIORst, HwIOClk
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.utils import HwIO_pack
from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.fifoDrop import HandshakedFifoDrop


@serializeParamsUniq
class Axi4SFifoDrop(Axi4SCompBase, HandshakedFifoDrop):
    """
    Synchronous FIFO for axi-stream interface with frame drop functionality
    and speculative buffering. Also known as a speculative FIFO.

    :note: DEPTH > axis.MAX_FRAME_LEN

    :see: :class:`hwtLib.handshaked.fifo_drop.HandshakedFifoDrop`

    .. hwt-autodoc:: _example_Axi4SFifoDrop
    """

    REG_CLS = NotImplementedError

    @override
    def hwDeclr(self):
        HandshakedFifo.hwDeclr(self)
        self.dataIn_discard = HwIOSignal()

    @override
    def hwImpl(self, clk_rst: Optional[Tuple[
            Tuple[HwIOClk, Union[HwIORst, HwIORst_n]],
            Tuple[HwIOClk, Union[HwIORst, HwIORst_n]]]]=None):
        super(HandshakedFifoDrop, self).hwImpl(clk_rst=clk_rst)

    def _connect_fifo_in(self):
        rd = self.get_ready_signal
        vld = self.get_valid_signal

        din = self.dataIn
        fIn = self.fifo.dataIn
        wr_en = ~fIn.wait
        rd(din)(wr_en)
        fIn.discard(self.dataIn_discard)
        fIn.commit(din.valid & din.last)
        fIn.data(HwIO_pack(din, exclude=[vld(din), rd(din)]))
        fIn.en(vld(din) & wr_en)


def _example_Axi4SFifoDrop():
    m = Axi4SFifoDrop()
    m.DEPTH = 4
    m.EXPORT_SIZE = True
    m.EXPORT_SPACE = True
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4SFifoDrop()

    print(to_rtl_str(m))
