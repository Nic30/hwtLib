from hwt.synthesizer.interface import Interface
from hwt.interfaces.std import Clk, VectSignal, Signal
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class MiiRxChannel(Interface):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.d = VectSignal(4)
        self.dv = Signal()
        self.er = Signal()


class MiiTxChannel(Interface):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.d = VectSignal(4)
        self.en = Signal()
        self.er = Signal()


class Mii(Interface):
    """
    Media Independent Interface

    PHY-MAC interface for <=100BASE Ethernet

    .. hwt-autodoc::
    """

    def _declr(self):
        self.rx_clk = Clk(masterDir=DIRECTION.IN)
        with self._associated(clk=self.rx_clk):
            self.rx = MiiRxChannel(masterDir=DIRECTION.IN)

        self.tx_clk = Clk(masterDir=DIRECTION.IN)
        with self._associated(clk=self.tx_clk):
            self.tx = MiiTxChannel()

    def _getIpCoreIntfClass(self):
        return IP_Mii


class IP_Mii(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "mii"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            "tx": {
                "d": "TXD",
                "en": "TX_EN",
                "er": "TX_ER",
            },
            "rx": {
                "d": "RXD",
                "dv": "RX_DV",
                "er": "RX_ER",
            },
            "tx_clk": "TX_CLK",
            "rx_clk": "RX_CLK",
        }
