from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal, HwIOClk
from hwt.pyUtils.typingFuture import override
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class GmiiTxChannel(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.d = HwIOVectSignal(8)
        self.en = HwIOSignal()
        self.er = HwIOSignal()


class GmiiRxChannel(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.d = HwIOVectSignal(8)
        self.dv = HwIOSignal()
        self.er = HwIOSignal()


class Gmii(HwIO):
    """
    Gigabit media independent interface
    Used to connect 1G Ethernet MAC and PHY

    :note: There is also variant with GTX_CLK, this version uses
        only single TX clock provided from MAC to PHY
    """

    @override
    def hwDeclr(self):
        self.rx_clk = HwIOClk(masterDir=DIRECTION.IN)
        with self._associated(clk=self.rx_clk):
            self.rx = GmiiRxChannel(masterDir=DIRECTION.IN)
        self.tx_clk = HwIOClk()
        with self._associated(clk=self.tx_clk):
            self.tx = GmiiTxChannel()

    @override
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
