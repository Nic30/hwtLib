from typing import Optional, Tuple, Union

from hwt.hwIOs.std import HwIOSignal, HwIORst, HwIORst_n, HwIOClk
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifoDrop import FifoDrop
from hwt.pyUtils.typingFuture import override


class HandshakedFifoDrop(HandshakedFifo):
    """
    FIFO for handsahaked interface which allows to discard/commit written data

    :see: :class:`hwtLib.handshaked.fifo.HandshakedFifo`
        and :class:`hwtLib.mem.fifoDrop.FifoDrop`

    .. hwt-autodoc:: _example_HandshakedFifoDrop
    """
    FIFO_CLS = FifoDrop

    @override
    def hwDeclr(self):
        HandshakedFifo.hwDeclr(self)
        self.dataIn_discard = HwIOSignal()
        self.dataIn_commit = HwIOSignal()

    @override
    def hwImpl(self, clk_rst: Optional[Tuple[
            Tuple[HwIOClk, Union[HwIORst, HwIORst_n]],
            Tuple[HwIOClk, Union[HwIORst, HwIORst_n]]]]=None):
        super(HandshakedFifoDrop, self).hwImpl(clk_rst=clk_rst)
        f = self.fifo
        f.dataIn.commit(self.dataIn_commit)
        f.dataIn.discard(self.dataIn_discard)


def _example_HandshakedFifoDrop():
    from hwt.hwIOs.std import HwIODataRdVld
    
    m = HandshakedFifoDrop(HwIODataRdVld)
    m.DEPTH = 8
    m.DATA_WIDTH = 4
    m.EXPORT_SIZE = True
    m.EXPORT_SPACE = True
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = _example_HandshakedFifoDrop()
    print(to_rtl_str(m))