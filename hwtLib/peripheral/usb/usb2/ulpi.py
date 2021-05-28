from hwt.code import Concat
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Signal
from hwt.interfaces.tristate import TristateSig
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.peripheral.usb.constants import USB_PID
from hwtLib.peripheral.usb.usb2.utmi import utmi_function_control_t, \
    utmi_interface_control_t, utmi_otg_control_t, utmi_interrupt_t
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta
from pyMathBitPrecise.bit_utils import mask


class ULPI_TX_CMD():
    NOOP = 0b00_000000
    """
    :cvar NOOP: Transmit USB data that does not have a USB_PID, such as
        chirp and resume signalling. The PHY starts
        transmitting on the USB beginning with the next data
        byte.
    """
    NOPID = 0b01_000000

    @staticmethod
    def is_USB_PID(packet_first_byte):
        if isinstance(packet_first_byte, int):
            return (packet_first_byte >> 4) == 0b01_00
        else:
            return packet_first_byte[:4]._eq(0b01_00)

    @staticmethod
    def get_USB_PID(packet_first_byte):
        if isinstance(packet_first_byte, int):
            return packet_first_byte & mask(4)
        else:
            return packet_first_byte[4:0]

    @staticmethod
    def USB_PID(pid: USB_PID):
        """
        Transmit USB packet. data(3:0) indicates USB
        packet identifier USB_PID(3:0).
        """
        if pid is None or isinstance(pid, int):
            pid = Bits(4).from_py(pid)
        else:
            assert pid._dtype.bit_length() == 4
        return Concat(Bits(4).from_py(0b01_00), pid)

    @staticmethod
    def REGW(addr):
        """
        Register write command with 6-bit immediate address.
        """
        if addr is None or isinstance(addr, int):
            addr = Bits(6).from_py(addr)
        else:
            assert addr._dtype.bit_length() == 6
        return Concat(Bits(2).from_py(0b10), addr)

    """
    :cvar Extended reqister write command. 8-bit address
        available in the next cycle.
    """
    EXTW = 0b10_101111

    """
    :cvar REGR: Register read command with 6-bit immediate
        address.
    """

    @staticmethod
    def REGR(addr):
        if addr is None or isinstance(addr, int):
            addr = Bits(6).from_py(addr)
        else:
            assert addr._dtype.bit_length() == 6
        return Concat(Bits(2).from_py(0b11), addr)

    """
    :cvar EXTR: Extended register read command. 8-bit address
        available in the next cycle.
    """
    EXTR = 0b11_101111

# class ULPI_RX_CMD():
#
#    def build(self, LineState, vBusState, RxEvent, ID, alt_int):


class ULPI_REG:
    """
    :note: all registers are 8b in size
    """
    Vendor_ID_Low = 0x00
    Vendor_ID_High = 0x01
    Product_ID_Low = 0x02
    Product_ID_High = 0x03

    Function_Control = 0x04
    Interface_Control = 0x07
    OTG_Control = 0x0A
    USB_Interrupt_Enable_Rising = 0x0D
    USB_Interrupt_Enable_Falling = 0x10
    USB_Interrupt_Status = 0x13
    USB_Interrupt_Latch = 0x14
    Debug = 0x15
    Scratch_Register = 0x16
    # optional registers
    Carkit_Control = 0x19
    Carkit_Interrupt_Delay = 0x1C
    Carkit_Interrupt_Enable = 0x1D
    Carkit_Interrupt_Status = 0x20
    Carkit_Interrupt_Latch = 0x21
    Carkit_Pulse_Control = 0x22
    Transmit_Positive_Width = 0x25
    Transmit_Negative_Width = 0x26
    Receive_Polarity_Recovery = 0x27

    REGS_WITH_SET_AND_CLR = [
        Function_Control,
        Interface_Control,
        OTG_Control,
        USB_Interrupt_Enable_Rising,
        USB_Interrupt_Enable_Falling,
        Scratch_Register,
        Carkit_Control,
        Carkit_Interrupt_Enable,
        Carkit_Pulse_Control,
    ]

    @classmethod
    def set_of(addr):
        """
        By write to this address the pattern on the data bus
        is OR’d with and written into the register.
        """
        assert addr in ULPI_REG.REGS_WITH_SET_AND_CLR, addr
        return addr + 1

    def clr_of(self, addr):
        """
        By write to this address the pattern on the data bus
        is a mask. If a bit in the mask is set, then
        the corresponding register bit will be set to zero (cleared).
        """
        assert addr in ULPI_REG.REGS_WITH_SET_AND_CLR, addr
        return addr + 2


ulpi_reg_function_control_t = utmi_function_control_t
ulpi_reg_function_control_t_reset_default = {
    "XcvrSelect": 1,
    "TermSelect": 0,
    "OpMode": 0,
    "Reset": 0,
    "SuspendM": 1,
}

ulpi_reg_interface_control_t = utmi_interface_control_t

ulpi_reg_otg_control_t = utmi_otg_control_t
ulpi_reg_otg_control_t_reset_defaults = {
    "IdPullup": 0,
    "DpPulldown": 1,
    "DmPulldown": 1,
    "DischrgVbus": 0,
    "ChrgVbus": 0,
    "DrvVbus": 0,
    "DrvVbusExternal": 0,
    "UseExternalVbusIndicator": 0,
}

ulpi_reg_usb_interrupt_enable_rising_t = \
ulpi_reg_usb_interrupt_enable_falling_t = \
ulpi_reg_usb_interrupt_status_t = \
ulpi_reg_usb_interrupt_latch_t = utmi_interrupt_t
ulpi_reg_usb_interrupt_status_t_reset_default = {
    "HostDisconnect": 0,
    "VbusValid": 0,
    "SessValid": 0,
    "SessEnd": 0,
    "IdGnd": 0,
}

ulpi_reg_debug_t = HStruct(
    (BIT, "LineState0"),
    (BIT, "LineState1"),
    (Bits(6), None),
)


class Ulpi(Interface):
    """
    ULPI (UTMI+ Low Pin Interface for USB2.0 PHY)

    * https://www.sparkfun.com/datasheets/Components/SMD/ULPI_v1_1.pdf

    :ivar ~.data: Bi-directional data bus, driven low by the Link during idle.
        Bus ownership is determined by dir. The Link and PHY initiate data
        transfers by driving a non-zero pattern onto the data bus.
        LPI defines interface timing for single-edge data transfers
        with respect to rising edge of clock. An implementation
        may optionally define double-edge data transfers
        with respect to both rising and falling edges of clock.
    :ivar ~.dir: Direction. Controls the direction of the data bus.
        When the PHY has data to transfer to the Link, it drives dir high
        to take ownership of the bus. When the PHY has no data to transfer it
        drives dir low and monitors the bus for Link activity.
        The PHY pulls dir high whenever the interface cannot accept data from the Link.
        For example, when the internal PHY PLL is not stable.
    :ivar ~.stp: Stop. The Link asserts this signal for 1 clock cycle to stop the data stream
        currently on the bus. If the Link is sending data to the PHY,
        stp indicates the last byte of data was on the bus in the previous cycle.
        If the PHY is sending data to the Link, stp forces the PHY to end its transfer,
        de-assert dir and relinquish control of the the data bus to the Link.
        (In the tx stp=1 is asserted after last word, data with stp=1 and after are interpreted as idle (until dir changes).)
    :ivar ~.nxt: Next. The PHY asserts this signal to throttle the data.
        When the Link is sending data to the PHY, nxt indicates when the current byte
        has been accepted by the PHY. The Link places the next byte on the data bus
        in the following clock cycle. When the PHY is sending data to the Link,
        nxt indicates when a new byte is available for the Link to consume.
        (In the rx nxt=0 means the transaction is paused and rx_cmd word is send instead of data.)


    :note: PHY is the master

    .. hwt-autodoc::
    """

    class DIR:
        """
        :note: if dir == PHY the data flows to PHY
        """
        PHY = 1
        LINK = 0

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        # the "t" has to be driven from outside of PHY (from Link usually implemented in FPGA)
        self.data = TristateSig(masterDir=DIRECTION.IN)
        self.data.DATA_WIDTH = self.DATA_WIDTH
        self.dir = Signal()
        self.stp = Signal(masterDir=DIRECTION.IN)
        self.nxt = Signal()

    def _getIpCoreIntfClass(self):
        return IP_Ulpi

    def _initSimAgent(self, sim:HdlSimulator):
        from hwtLib.peripheral.usb.usb2.ulpi_agent import UlpiAgent
        self._ag = UlpiAgent(sim, self)


class IP_Ulpi(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "ulpi"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            # 'clk': "CLK", # [todo] need to reference associated clk/rst
            # 'rst': "RST",
            'dir': 'DIR',
            "nxt": 'NEXT',
            'stp': "STOP",
            'data': {
                'i': 'DATA_I',
                'o': 'DATA_O',
                't': 'DATA_T',
            },
        }
