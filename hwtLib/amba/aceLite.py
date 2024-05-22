from hwt.hwIOs.std import HwIOVectSignal
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4Lite import Axi4Lite, Axi4Lite_addr
from hwtSimApi.hdlSimulator import HdlSimulator


#################################################################
class AceLite_addr(Axi4Lite_addr):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        Axi4Lite_addr.hwDeclr(self)
        self.domain = HwIOVectSignal(2)
        self.snoop = HwIOVectSignal(3)
        self.bar = HwIOVectSignal(2)

    @override
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

    @override
    def _getIpCoreIntfClass(self):
        raise NotImplementedError()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()
