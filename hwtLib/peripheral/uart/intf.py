from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOSignal
from hwt.pyUtils.typingFuture import override
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class Uart(HwIO):
    """
    Base UART interface, also known as Serial or COM.

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.rx = HwIOSignal(masterDir=DIRECTION.IN)
        self.tx = HwIOSignal()

    @override
    def _getIpCoreIntfClass(self):
        return IP_Uart


class IP_Uart(IntfIpMeta):
    def __init__(self):
        super().__init__()
        self.name = "uart"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            'rx': "RxD",
            'tx': "TxD"
        }
