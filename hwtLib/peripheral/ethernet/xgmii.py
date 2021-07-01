from typing import List

from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import VectSignal, Clk
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class XgmiiChannel(Interface):
    """
    :ivar ~.clk: clock signal
    :ivar ~.d: data signal
    :ivar ~.c: control signal
    :ivar ~.IS_DDR: if True, the clock is used as double-data-rate clock
        (read/write data on rising and falling edge of clk)
    :ivar ~.ALIGNMENT: specifies alignment of the start of the packet
        1 means packet can start anywhere 4 for 8B wide interface means
        that packet can start at lane 0 or 4

    .. hwt-autodoc::
    """

    class CONTROL:
        """
        Enum to name meanings of the bit values in "c" signal.
        """
        DATA = 0
        CONTROL = 1

    class CMD:
        """
        This is an enum of values which may appear
        on data byte while corresponding control bit is :py:attr:`~.CONTROL.CONTROL`
        """
        IDLE = Bits(8).from_py(0x07)
        START = Bits(8).from_py(0xFB)
        TERM = Bits(8).from_py(0xFD)
        ERROR = Bits(8).from_py(0xFE)

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.FREQ = Param(int(156.25e6))
        self.IS_DDR = Param(True)
        self.ALIGNMENT = Param(1)

    def _declr(self):
        assert self.ALIGNMENT > 0 and self.ALIGNMENT < self.DATA_WIDTH // 8, self.ALIGNMENT
        self.clk = Clk()
        self.clk.FREQ = self.FREQ
        self._make_association(clk=self.clk)
        self.d = VectSignal(self.DATA_WIDTH)
        self.c = VectSignal(self.DATA_WIDTH // 8)

    def detect_control(self, s) -> List[RtlSignal]:
        """
        :returns: a list of signals which are 1 if the specified control signal
            was detected on that specific byte, detector for byte 0 first in output list
        """
        d = self.d
        c = self.c
        return [
            c[i]._eq(self.CONTROL.CONTROL) & d[(i + 1) * 8:i * 8]._eq(s)
            for i in range(self.DATA_WIDTH // 8)
        ]


class Xgmii(Interface):
    """
    10G Media Independent Interface

    :note: usually 64b@156.25MHz DDR or 32b@312.5MHz DDR
        or twice wider and SDR

    :note: XLGMII/CGMII (40G/100G) interfaces are just scaled up version of this interface

    .. hwt-autodoc::
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
