from typing import Optional, Tuple, Union

from hwt.interfaces.std import Signal, Rst, Rst_n, Clk
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifoDrop import FifoDrop


class HandshakedFifoDrop(HandshakedFifo):
    """
    Fifo for handsahaked interface which allows to discard/commit written data

    :see: :class:`hwtLib.handshaked.fifo.HandshakedFifo`
        and :class:`hwtLib.mem.fifoDrop.FifoDrop`

    .. hwt-autodoc:: _example_HandshakedFifoDrop
    """
    FIFO_CLS = FifoDrop

    def _declr(self):
        HandshakedFifo._declr(self)
        self.dataIn_discard = Signal()
        self.dataIn_commit = Signal()

    def _impl(self, clk_rst: Optional[Tuple[
            Tuple[Clk, Union[Rst, Rst_n]],
            Tuple[Clk, Union[Rst, Rst_n]]]]=None):
        super(HandshakedFifoDrop, self)._impl(clk_rst=clk_rst)
        f = self.fifo
        f.dataIn.commit(self.dataIn_commit)
        f.dataIn.discard(self.dataIn_discard)


def _example_HandshakedFifoDrop():
    from hwt.interfaces.std import Handshaked
    u = HandshakedFifoDrop(Handshaked)
    u.DEPTH = 8
    u.DATA_WIDTH = 4
    u.EXPORT_SIZE = True
    u.EXPORT_SPACE = True
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HandshakedFifoDrop()
    print(to_rtl_str(u))