from hwt.constants import DIRECTION
from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal, HwIORdVldSync
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtSimApi.hdlSimulator import HdlSimulator


class Axi_id(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self, default_id_width=0):
        self.ID_WIDTH = HwParam(default_id_width)

    @override
    def hwDeclr(self):
        if self.ID_WIDTH:
            self.id = HwIOVectSignal(self.ID_WIDTH)


class Axi_user(HwIO):

    @override
    def hwConfig(self):
        self.USER_WIDTH:int = HwParam(0)

    @override
    def hwDeclr(self):
        if self.USER_WIDTH:
            self.user = HwIOVectSignal(self.USER_WIDTH)


class Axi_strb(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        self.strb = HwIOVectSignal(self.DATA_WIDTH // 8)


class Axi_hs(HwIORdVldSync):
    """
    AXI handshake interface with ready and valid signal
    (same as HwIORdVldSync just vld is valid and rd is ready)
    transaction happens when both ready and valid are high

    :ivar ~.ready: when high slave is ready to receive data
    :ivar ~.valid: when high master is sending data to slave

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.ready = HwIOSignal(masterDir=DIRECTION.IN)
        self.valid = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


def AxiMap(prefix, listOfNames, d=None):
    if d is None:
        d = {}

    for n in listOfNames:
        d[n] = (prefix + n).upper()

    return d
