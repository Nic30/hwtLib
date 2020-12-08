#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, Optional, Union

from hwt.interfaces.std import Signal, Rst_n, Rst, Clk
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.fifoDrop import HandshakedFifoDrop


@serializeParamsUniq
class AxiSFifoDrop(AxiSCompBase, HandshakedFifoDrop):
    """
    Synchronous fifo for axi-stream interface with frame drop functionality
    and speculative buffering. Also known as a speculative fifo.

    :note: DEPTH > axis.MAX_FRAME_LEN

    :see: :class:`hwtLib.handshaked.fifo_drop.HandshakedFifoDrop`

    .. hwt-autodoc:: _example_AxiSFifoDrop
    """
    def _declr(self):
        HandshakedFifo._declr(self)
        self.dataIn_discard = Signal()

    def _impl(self, clk_rst: Optional[Tuple[
            Tuple[Clk, Union[Rst, Rst_n]],
            Tuple[Clk, Union[Rst, Rst_n]]]]=None):
        super(HandshakedFifoDrop, self)._impl(clk_rst=clk_rst)

    def _connect_fifo_in(self):
        rd = self.get_ready_signal
        vld = self.get_valid_signal

        din = self.dataIn
        fIn = self.fifo.dataIn
        wr_en = ~fIn.wait
        rd(din)(wr_en)
        fIn.discard(self.dataIn_discard)
        fIn.commit(din.valid & din.last)
        fIn.data(packIntf(din, exclude=[vld(din), rd(din)]))
        fIn.en(vld(din) & wr_en)


def _example_AxiSFifoDrop():
    u = AxiSFifoDrop()
    u.DEPTH = 4
    u.EXPORT_SIZE = True
    u.EXPORT_SPACE = True
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiSFifoDrop()

    print(to_rtl_str(u))
