from hwt.constants import DIRECTION
from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override


class LocalLink(HwIO):
    """
    Stream with "byte enable" and "start/end of frame/packet"

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        self.rem = HwIOVectSignal(log2ceil(self.DATA_WIDTH // 8))
        self.src_rdy_n = HwIOSignal()
        self.dst_rdy_n = HwIOSignal(masterDir=DIRECTION.IN)
        self.sof_n = HwIOSignal()
        self.eof_n = HwIOSignal()
        self.eop_n = HwIOSignal()
        self.sop_n = HwIOSignal()
