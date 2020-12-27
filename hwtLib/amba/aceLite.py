from hwt.interfaces.std import VectSignal
from hwtLib.amba.axi4Lite import Axi4Lite, Axi4Lite_addr
from hwtSimApi.hdlSimulator import HdlSimulator


#################################################################
class AceLite_addr(Axi4Lite_addr):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        Axi4Lite_addr._declr(self)
        self.domain = VectSignal(2)
        self.snoop = VectSignal(3)
        self.bar = VectSignal(2)

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


class AceLite(Axi4Lite):
    """
    AMBA ACE-lite interface

    https://static.docs.arm.com/ihi0022/d/IHI0022D_amba_axi_protocol_spec.pdf

    .. hwt-autodoc::
    """
    AR_CLS = AceLite_addr
    AW_CLS = AceLite_addr

    def _getIpCoreIntfClass(self):
        raise NotImplementedError()

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()
