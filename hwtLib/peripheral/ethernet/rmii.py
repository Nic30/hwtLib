from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal, HwIOClk
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.peripheral.ethernet.rmii_agent import RmiiAgent, RmiiTxChannelAgent, \
    RmiiRxChannelAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class RmiiTxChannel(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(2)

    @override
    def hwDeclr(self):
        self.d = HwIOVectSignal(self.DATA_WIDTH)
        self.en = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RmiiTxChannelAgent(sim, self)


class RmiiRxChannel(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(2)

    @override
    def hwDeclr(self):
        self.d = HwIOVectSignal(self.DATA_WIDTH)
        self.crs_dv = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RmiiRxChannelAgent(sim, self)


class Rmii(HwIO):
    """
    Reduced Media Independent HwIO

    off-chip PHY-MAC interface for <=100BASE Ethernet

    :ivar ~.crs_dc: carrier sense/ rx data valid
    :ivar ~.md: interface for configuration and identification of PHY

    :note: 50Mhz reference clock may be an input on both devices from an external
        clock source, or may be driven from the MAC to the PHY
    :note: ref_clk operates on 50MHZ in both 100M/10M mode however
        in 10M mode data have to stay valid for 10 clk cycles

    .. hwt-autodoc::
    """


    @override
    def hwConfig(self):
        self.CLK_MASTER_DIR = HwParam(DIRECTION.IN)
        self.FREQ = HwParam(int(50e6))
        self.DATA_WIDTH = HwParam(2)

    @override
    def hwDeclr(self):
        self.ref_clk = HwIOClk(masterDir=self.CLK_MASTER_DIR)
        self.ref_clk.FREQ = self.FREQ
        with self._hwParamsShared():
            with self._associated(clk=self.ref_clk):
                self.tx = RmiiTxChannel()
                self.rx = RmiiRxChannel(masterDir=DIRECTION.IN)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RmiiAgent(sim, self)


class IP_Rmii(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "rmii"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            "tx": {
                "d": "TXD",
                "en": "TX_EN",
            },
            "rx": {
                "d": "RXD",
                "crs_dv": "CRS_DV",
            },
        }
