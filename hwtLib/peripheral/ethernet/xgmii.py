from typing import List

from hwt.hdl.types.bits import HBits
from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOVectSignal, HwIOClk
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class XgmiiChannel(HwIO):
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
        IDLE = HBits(8).from_py(0x07)
        START = HBits(8).from_py(0xFB)
        TERM = HBits(8).from_py(0xFD)
        ERROR = HBits(8).from_py(0xFE)

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)
        self.CLK_FREQ = HwParam(int(156.25e6))
        self.IS_DDR = HwParam(True)
        self.ALIGNMENT = HwParam(1)

    @override
    def hwDeclr(self):
        assert self.ALIGNMENT > 0 and self.ALIGNMENT < self.DATA_WIDTH // 8, self.ALIGNMENT
        self.clk = HwIOClk()
        self.clk.FREQ = self.CLK_FREQ
        self._make_association(clk=self.clk)
        self.d = HwIOVectSignal(self.DATA_WIDTH)
        self.c = HwIOVectSignal(self.DATA_WIDTH // 8)

    def detect_control(self, s) -> List[RtlSignal]:
        """
        :return: a list of signals which are 1 if the specified control signal
            was detected on that specific byte, detector for byte 0 first in output list
        """
        d = self.d
        c = self.c
        return [
            c[i]._eq(self.CONTROL.CONTROL) & d[(i + 1) * 8:i * 8]._eq(s)
            for i in range(self.DATA_WIDTH // 8)
        ]


class Xgmii(HwIO):
    """
    10G Media Independent HwIO

    :note: usually 64b@156.25MHz DDR or 32b@312.5MHz DDR
        or twice wider and SDR

    :note: XLGMII/CGMII (40G/100G) interfaces are just scaled up version of this interface

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        XgmiiChannel.hwConfig(self)

    @override
    def hwDeclr(self):
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
