from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal, Signal, HandshakeSync
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtSimApi.hdlSimulator import HdlSimulator


class Axi_id(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self, default_id_width=0):
        self.ID_WIDTH = Param(default_id_width)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)


class Axi_user(Interface):

    def _config(self):
        self.USER_WIDTH = Param(0)

    def _declr(self):
        if self.USER_WIDTH:
            self.user = VectSignal(self.USER_WIDTH)


class Axi_strb(Interface):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.strb = VectSignal(self.DATA_WIDTH // 8)


class Axi_hs(HandshakeSync):
    """
    AXI handshake interface with ready and valid signal
    (same as HandshakeSync just vld is valid and rd is ready)
    transaction happens when both ready and valid are high

    :ivar ~.ready: when high slave is ready to receive data
    :ivar ~.valid: when high master is sending data to slave

    .. hwt-autodoc::
    """
    def _declr(self):
        self.ready = Signal(masterDir=DIRECTION.IN)
        self.valid = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


def AxiMap(prefix, listOfNames, d=None):
    if d is None:
        d = {}

    for n in listOfNames:
        d[n] = (prefix + n).upper()

    return d
