from hwt.interfaces.std import Clk, VectSignal, Signal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class RgmiiChannel(Interface):
    """
    :note: clk.FREQ can be 125 MHz, 25 MHz, or 2.5 MHz
        with ±50 ppm tolerance based on the selected speed.

    .. hwt-autodoc::
    """

    def _config(self):
        self.FREQ = Param(int(125e6))

    def _declr(self):
        self.clk = Clk()
        self.clk.FREQ = self.FREQ
        with self._associated(clk=self.clk):
            self.d = VectSignal(4)
            self.ctl = Signal()


class Rgmii(Interface):
    """
    Reduced Gigabit Media Independent interface
    Used to off-chip commect 1G Ethernet MAC and PHY

    :note: There is also version of this interface where
        for 10M/100M the tx_clk provided by PHY is used
        in 1G mode the tx_gclk provided by MAC is used

    .. hwt-autodoc::
    """


    def _config(self):
        RgmiiChannel._config(self)

    def _declr(self):
        with self._paramsShared():
            self.rx = RgmiiChannel(masterDir=DIRECTION.IN)
            self.tx = RgmiiChannel()

    def _getIpCoreIntfClass(self):
        return IP_Rgmii


class IP_Rgmii(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "rgmii"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            "tx": {
                "d": "TD",
                "ctl": "TX_CTL",
                "clk": "TXC",
            },
            "rx": {
                "d": "RD",
                "ctl": "RX_CTL",
                "clk": "RXC",
            },
        }
