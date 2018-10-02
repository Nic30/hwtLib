from hwt.interfaces.std import D, Signal
from ipCorePackager.intfIpMeta import IntfIpMeta
from hwt.synthesizer.interface import Interface


class Uart(Interface):
    """
    Base UART interface, also known as Serial or COM.
    """

    def _declr(self):
        self.rx = Signal(masterDir=D.IN)
        self.tx = Signal()

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
