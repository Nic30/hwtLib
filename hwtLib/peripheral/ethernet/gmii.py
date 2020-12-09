from hwt.interfaces.std import VectSignal, Signal, Clk
from hwt.synthesizer.interface import Interface
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class GmiiTxChannel(Interface):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.d = VectSignal(8)
        self.en = Signal()
        self.er = Signal()


class GmiiRxChannel(Interface):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.d = VectSignal(8)
        self.dv = Signal()
        self.er = Signal()


class Gmii(Interface):
    """
    Gigabit media independent interface
    Used to connect 1G Ethernet MAC and PHY

    :note: There is also variant with GTX_CLK, this version uses
        only single TX clock provided from MAC to PHY
    """

    def _declr(self):
        self.rx_clk = Clk(masterDir=DIRECTION.IN)
        with self._associated(clk=self.rx_clk):
            self.rx = GmiiRxChannel(masterDir=DIRECTION.IN)
        self.tx_clk = Clk()
        with self._associated(clk=self.tx_clk):
            self.tx = GmiiTxChannel()

    def _getIpCoreIntfClass(self):
        return IP_Gmii


class IP_Gmii(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "gmii"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            "tx": {
                "d": "TXD",
                "en": "TX_EN",
                "er": "TX_ER",
            },
            "tx": {
                "d": "RXD",
                "dv": "RX_DV",
                "er": "RX_ER",
            },
            "tx_clk": "TX_CLK",
            "rx_clk": "RX_CLK",
        }
