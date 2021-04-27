from hwt.code import Concat
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal
from hwt.interfaces.tristate import TristateSig
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from ipCorePackager.constants import DIRECTION
from ipCorePackager.intfIpMeta import IntfIpMeta
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.defs import BIT
from hwtLib.peripheral.usb.utmi import utmi_function_control_t, \
    utmi_interface_control_t, utmi_otg_control_t, utmi_interrupt_t
from hwt.simulator.agentBase import SyncAgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.triggers import WaitWriteOnly, WaitCombRead
from hwt.hdl.constants import NOP
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

    """
    :cvar USB_PID: Transmit USB packet. data(3:0) indicates USB
        packet identifier USB_PID(3:0).
    """

    @staticmethod
    def USB_PID(pid):
        if pid is None or isinstance(pid, int):
            pid = Bits(4).from_py(pid)
        else:
            assert pid._dtype.bit_length() == 4
        return Concat(Bits(4).from_py(0b01_00), pid)

    """
    :cvar REGW: Register write command with 6-bit immediate
        address.
    """

    @staticmethod
    def REGW(addr):
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
    :ivar ~.nxt: Next. The PHY asserts this signal to throttle the data.
        When the Link is sending data to the PHY, nxt indicates when the current byte
        has been accepted by the PHY. The Link places the next byte on the data bus
        in the following clock cycle. When the PHY is sending data to the Link,
        nxt indicates when a new byte is available for the Link to consume.


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
        self._ag = UlpiAgent(sim, self)


class UlpiAgent(SyncAgentBase):
    """
    :note: the RX is always from PHY to Link
        the TX is always from Link to PHY
    """

    def __init__(self, sim:HdlSimulator, intf, allowNoReset=False,
        wrap_monitor_and_driver_in_edge_callback=True):
        SyncAgentBase.__init__(self, sim, intf, allowNoReset=allowNoReset, wrap_monitor_and_driver_in_edge_callback=wrap_monitor_and_driver_in_edge_callback)
        self.link_to_phy_packets = []
        self.phy_to_link_packets = []

        self.actual_link_to_phy_packet = []
        self.actual_phy_to_link_packet = []
        self.actual_phy_to_link_data = NOP

        self.dir = Ulpi.DIR.PHY
        self.in_turnarround = False
        self.reg_interrupt = ulpi_reg_usb_interrupt_status_t.from_py(ulpi_reg_usb_interrupt_status_t_reset_default)
        self.RxEvent_RxActive = 0
        self.RxEvent_RxError = 0
        self.HostDisconnected = 0

    def on_link_to_phy_packet(self, packet: list):
        # [TODO] could be register write/read which needs to be processed
        self.link_to_phy_packets.append(packet)

    def build_RX_CMD(self):
        LineState = 0b00 # SE0
        inter = self.reg_interrupt
        if inter.SessEnd & ~inter.SessValid & ~inter.VbusValid:
            VbusSate = 0b00
        elif ~inter.SessEnd & ~inter.SessValid & ~inter.VbusValid:
            VbusSate = 0b01
        elif inter.SessValid & ~inter.VbusValid:
            VbusSate = 0b10
        elif inter.VbusValid:
            VbusSate = 0b11
        RxActive = self.RxEvent_RxActive
        RxError = self.RxEvent_RxError
        HostDisconnected = self.HostDisconnected
        if ~RxActive and ~RxError and ~HostDisconnected:
            RxEvent = 0b00
        elif RxActive and ~RxError and ~HostDisconnected:
            RxEvent = 0b01
        elif RxActive and RxError and ~HostDisconnected:
            RxEvent = 0b11
        elif HostDisconnected:
            RxEvent = 0b10
        IdGnd = 0
        alt_int = 0
        return (alt_int << 7) | (IdGnd << 6) | (RxEvent << 4) | (VbusSate << 2) | LineState

    def data_write(self, v):
        if v is NOP:
            v = self.build_RX_CMD()
        self.intf.data.i._sigInside.write()

    def data_read(self):
        return self.intf.data.o._sigInside.read()

    def driver(self):
        """
        Drive ULPI interface as a PHY does
        """
        intf = self.intf
        yield WaitWriteOnly()
        if self.in_turnarround:
            # entirely skip the turnaround cycle
            self.in_turnarround = False
            return

        intf.dir._sigInside.write(self.dir)
        yield WaitCombRead()
        stp = intf.stp._sigInside.read()
        try:
            stp = int(stp)
        except ValueError:
            raise AssertionError(
                ("%r: stp signal for interface %r is in invalid state,"
                 " this would cause desynchronization") %
                (self.sim.now, intf))

        en = self.notReset() and self._enabled
        intf.nxt._sigInside.write(int(en and not stp))
        if not en:
            return

        t = intf.data.t._sigInside.read()
        if self.dir == Ulpi.DIR.PHY:
            # RX from PHY
            assert int(t) == 0, (t, "link must not write data when PHY is the master")

            if not stp:
                # some data in packet, if NOP sending RX_CMD
                if not self.actual_phy_to_link_packet and self.phy_to_link_packets:
                    self.actual_phy_to_link_packet = self.phy_to_link_packets.popleft()

                if self.actual_phy_to_link_data is NOP and self.actual_phy_to_link_packet:
                    self.actual_phy_to_link_data = self.actual_phy_to_link_packet.popleft()
                else:
                    self.actual_phy_to_link_data = NOP

                self.data_write(self.actual_phy_to_link_data)

        else:
            # TX to PHY
            assert int(t) == mask(8), (t, "link must write data when it is the master")

            if stp:
                # end of packet, the current data is not valid
                self.on_link_to_phy_packet(self.actual_link_to_phy_packet)

                self.actual_link_to_phy_packet = []
                self.dir = Ulpi.DIR.LINK
                self.in_turnarround = True
            else:
                self.actual_link_to_phy_packet.append(self.data_read())


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
