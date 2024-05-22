from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOClk, HwIOVectSignal, HwIOSignal
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class MiiRxChannel(HwIO):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.d = HwIOVectSignal(4)
        self.dv = HwIOSignal()
        self.er = HwIOSignal()


class MiiTxChannel(HwIO):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.d = HwIOVectSignal(4)
        self.en = HwIOSignal()
        self.er = HwIOSignal()


class Mii(HwIO):
    """
    Media Independent HwIO

    PHY-MAC interface for <=100BASE Ethernet

    .. hwt-autodoc::
    """

    def _declr(self):
        self.rx_clk = HwIOClk(masterDir=DIRECTION.IN)
        with self._associated(clk=self.rx_clk):
            self.rx = MiiRxChannel(masterDir=DIRECTION.IN)

        self.tx_clk = HwIOClk(masterDir=DIRECTION.IN)
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
