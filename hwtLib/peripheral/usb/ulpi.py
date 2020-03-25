from hwt.interfaces.std import Signal, Clk, Rst
from hwt.interfaces.tristate import TristateSig
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta


class Ulpi(Interface):
    """
    Interface for USB2.0 PHY

    * https://www.sparkfun.com/datasheets/Components/SMD/ULPI_v1_1.pdf

    :ivar data: Bi-directional data bus, driven low by the Link during idle.
        Bus ownership is determined by dir. The Link and PHY initiate data
        transfers by driving a non-zero pattern onto the data bus.
        LPI defines interface timing for single-edge data transfers
        with respect to rising edge of clock. An implementation
        may optionally define double-edge data transfers
        with respect to both rising and falling edges of clock.
    :ivar dir: Direction. Controls the direction of the data bus.
        When the PHY has data to transfer to the Link, it drives dir high
        to take ownership of the bus. When the PHY has no data to transfer it
        drives dir low and monitors the bus for Link activity.
        The PHY pulls dir high whenever the interface cannot accept data from the Link.
        For example, when the internal PHY PLL is not stable.
    :ivar stp: Stop. The Link asserts this signal for 1 clock cycle to stop the data stream
        currently on the bus. If the Link is sending data to the PHY,
        stp indicates the last byte of data was on the bus in the previous cycle.
        If the PHY is sending data to the Link, stp forces the PHY to end its transfer,
        de-assert dir and relinquish control of the the data bus to the Link.
    :ivar nxt: Next. The PHY asserts this signal to throttle the data.
        When the Link is sending data to the PHY, nxt indicates when the current byte
        has been accepted by the PHY. The Link places the next byte on the data bus
        in the following clock cycle. When the PHY is sending data to the Link,
        nxt indicates when a new byte is available for the Link to consume.
    """
    class DIR:
        PHY = 1
        LINK = 0

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.clk = Clk()
        self.rst = Rst()
        with self._associated(clk=self.clk, rst=self.rst):
            self.data = TristateSig()
            self.dir = Signal()
            self.stop = Signal(masterDir=DIRECTION.IN)
            self.next = Signal()

    def _getIpCoreIntfClass(self):
        return IP_Ulpi


class IP_Ulpi(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "ulpi"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            'clk': "CLK",
            'rst': "RST",
            'dir': 'DIR',
            "next": 'NEXT',
            'stop': "STOP",
            'data': {
                'i': 'DATA_I',
                'o': 'DATA_O',
                't': 'DATA_T',
            },
        }
