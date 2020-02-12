from hwt.hdl.typeShortcuts import vec
from hwt.interfaces.std import VectSignal, Clk
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class XgmiiChannel(Interface):
    """
    :ivar clk: clock signal
    :ivar d: data signal
    :ivar c: controll signal
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.FREQ = Param(int(156.25e6))

    def _declr(self):
        self.clk = Clk()
        self.clk.FREQ = self.FREQ
        self._make_association(clk=self.clk)
        self.d = VectSignal(self.DATA_WIDTH)
        self.c = VectSignal(self.DATA_WIDTH // 8)


class XGMII_CMD:
    IDLE = vec(0x07, 8)
    START = vec(0xFB, 8)
    TERM = vec(0xFD, 8)
    ERROR = vec(0xFE, 8)


class Xgmii(Interface):
    """
    10G Media Independent Interface

    :note: usually 64b@156.25MHz or 32b@312.5MHz
    """

    def _config(self):
        XgmiiChannel._config(self)

    def _declr(self):
        self.rx = XgmiiChannel(masterDir=DIRECTION.IN)
        self.tx = XgmiiChannel()


class IP_xgmii(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "xgmii"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            "tx": {
                "d": "TXD",
                "c": "TXC",
                "clk": "TX_CLK",
            },
            "rx": {
                "d": "RXD",
                "c": "RXC",
                "clk": "RX_CLK",
            },
        }
