from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOClk, HwIOVectSignal, HwIOSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class RgmiiChannel(HwIO):
    """
    :note: CLK_FREQ can be 125 MHz, 25 MHz, or 2.5 MHz
        with ±50 ppm tolerance based on the selected speed.

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.CLK_FREQ = HwParam(int(125e6))

    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        self.clk.FREQ = self.CLK_FREQ
        with self._associated(clk=self.clk):
            self.d = HwIOVectSignal(4)
            self.ctl = HwIOSignal()


class Rgmii(HwIO):
    """
    Reduced Gigabit Media Independent interface
    Used to off-chip commect 1G Ethernet MAC and PHY

    :note: There is also version of this interface where
        for 10M/100M the tx_clk provided by PHY is used
        in 1G mode the tx_gclk provided by MAC is used

    .. hwt-autodoc::
    """


    @override
    def hwConfig(self):
        RgmiiChannel.hwConfig(self)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            self.rx = RgmiiChannel(masterDir=DIRECTION.IN)
            self.tx = RgmiiChannel()

    @override
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
