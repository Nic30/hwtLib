from hwt.interfaces.std import VectSignal, Signal, Clk
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtLib.peripheral.ethernet.rmii_agent import RmiiAgent, RmiiTxChannelAgent,\
    RmiiRxChannelAgent


class RmiiTxChannel(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(2)

    def _declr(self):
        self.d = VectSignal(self.DATA_WIDTH)
        self.en = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RmiiTxChannelAgent(sim, self)


class RmiiRxChannel(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(2)

    def _declr(self):
        self.d = VectSignal(self.DATA_WIDTH)
        self.crs_dv = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RmiiRxChannelAgent(sim, self)


class Rmii(Interface):
    """
    Reduced Media Independent Interface

    off-chip PHY-MAC interface for <=100BASE Ethernet

    :ivar ~.crs_dc: carrier sense/ rx data valid
    :ivar ~.md: interface for configuration and identification of PHY

    :note: 50Mhz reference clock may be an input on both devices from an external
        clock source, or may be driven from the MAC to the PHY
    :note: ref_clk operates on 50MHZ in both 100M/10M mode however
        in 10M mode data have to stay valid for 10 clk cycles

    .. hwt-autodoc::
    """


    def _config(self):
        self.CLK_MASTER_DIR = Param(DIRECTION.IN)
        self.FREQ = Param(int(50e6))
        self.DATA_WIDTH = Param(2)

    def _declr(self):
        self.ref_clk = Clk(masterDir=self.CLK_MASTER_DIR)
        self.ref_clk.FREQ = self.FREQ
        with self._paramsShared():
            with self._associated(clk=self.ref_clk):
                self.tx = RmiiTxChannel()
                self.rx = RmiiRxChannel(masterDir=DIRECTION.IN)

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
