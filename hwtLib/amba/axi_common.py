from hwt.constants import DIRECTION
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal, HwIORdVldSync
from hwt.hwIO import HwIO
from hwt.hwParam import HwParam
from hwtSimApi.hdlSimulator import HdlSimulator


class Axi_id(HwIO):
    """
    .. hwt-autodoc::
    """

    def _config(self, default_id_width=0):
        self.ID_WIDTH = HwParam(default_id_width)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = HwIOVectSignal(self.ID_WIDTH)


class Axi_user(HwIO):

    def _config(self):
        self.USER_WIDTH:int = HwParam(0)

    def _declr(self):
        if self.USER_WIDTH:
            self.user = HwIOVectSignal(self.USER_WIDTH)


class Axi_strb(HwIO):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(64)

    def _declr(self):
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

    def _declr(self):
        self.ready = HwIOSignal(masterDir=DIRECTION.IN)
        self.valid = HwIOSignal()

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


def AxiMap(prefix, listOfNames, d=None):
    if d is None:
        d = {}

    for n in listOfNames:
        d[n] = (prefix + n).upper()

    return d
