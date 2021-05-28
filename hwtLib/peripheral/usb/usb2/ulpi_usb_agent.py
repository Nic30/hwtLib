from collections  import deque
from typing import Deque, Union

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwtLib.peripheral.usb.constants import USB_PID, usb_addr_t, usb_endp_t, \
    usb_crc5_t
from hwtLib.peripheral.usb.sim.agent_base import UsbPacketToken, UsbPacketData, \
    UsbPacketHandshake
from hwtLib.peripheral.usb.sim.usb_agent_device import UsbDevAgent
from hwtLib.peripheral.usb.sim.usb_agent_host import UsbHostAgent
from hwtLib.peripheral.usb.usb2.ulpi import ULPI_TX_CMD, Ulpi
from hwtLib.peripheral.usb.usb2.ulpi_agent import UlpiAgent
from hwtSimApi.hdlSimulator import HdlSimulator


class UlpiUsbHostProcAgent(UsbHostAgent):
    tx_packet_token_t = HStruct(
        (Bits(8), "cmd"),
        (usb_addr_t, "addr"),
        (usb_endp_t, "endp"),
        (usb_crc5_t, "crc5"),  # :note: not involves USB_PID, only addr, endp
    )

    def parse_packet(self, p: Deque[int]):
        # need to cut of ulpi tx_cmd header
        tx_cmd = p.popleft()
        if ULPI_TX_CMD.is_USB_PID(tx_cmd):
            pid = ULPI_TX_CMD.get_USB_PID(tx_cmd)
            if USB_PID.is_token(pid):
                return UsbPacketToken.from_pid_and_body_bytes(pid, p)
            elif USB_PID.is_data(pid):
                return UsbPacketData(pid, p)
            elif USB_PID.is_hs(pid):
                return UsbPacketHandshake(pid)
            else:
                raise NotImplementedError(pid)
        else:
            raise NotImplementedError(tx_cmd)

    def deparse_packet(self, p: Union[UsbPacketToken, UsbPacketData, UsbPacketHandshake]):
        cls = type(p)
        if cls is UsbPacketToken:
            v = self.tx_packet_token_t.from_py({
                "cmd": ULPI_TX_CMD.USB_PID(p.pid),
                "addr": p.addr,
                "endp": p.endp,
                "crc5": p.crc5(),
            })
            v = v._reinterpret_cast(Bits(8)[self.tx_packet_token_t.bit_length() // 8])
            v0 = deque()
            v0.extend(int(_v) for _v in v)
            return v0

        elif cls is UsbPacketData:
            v = deque()
            v.append(ULPI_TX_CMD.USB_PID(p.pid))
            v.extend(p.data)
            return v

        elif cls is UsbPacketHandshake:
            v = deque()
            v.append(ULPI_TX_CMD.USB_PID(p.pid))
            return v

        else:
            raise NotImplementedError(cls, p)


class UlpiUsbDevProcAgent(UsbDevAgent):

    def parse_packet(self, p):
        return UlpiUsbHostProcAgent.parse_packet(self, p)

    def deparse_packet(self, p):
        # need to add ulpi tx_cmd header
        return UlpiUsbHostProcAgent.deparse_packet(self, p)


class UlpiUsbAgent(UlpiAgent):
    """
    :class:`hwtLib.peripheral.usb.usb2.ulpi_agent.UlpiAgent`
    with device host logic and USB stack
    """

    def __init__(self, sim:HdlSimulator, intf:Ulpi, allowNoReset=False,
                 wrap_monitor_and_driver_in_edge_callback=True):
        UlpiAgent.__init__(self, sim, intf, allowNoReset=allowNoReset,
                           wrap_monitor_and_driver_in_edge_callback=wrap_monitor_and_driver_in_edge_callback)
        self.descriptors = None
        self.usb_driver = None
        self.usb_driver_proc = None

    def run_usb_driver(self):
        if self.usb_driver_proc is not None:
            try:
                next(self.usb_driver_proc)
            except StopIteration:
                pass

    def driver(self):
        self.run_usb_driver()
        yield from UlpiAgent.driver(self)
        self.run_usb_driver()

    def getDrivers(self):
        # PHY/host
        self.usb_driver = UlpiUsbHostProcAgent(self.link_to_phy_packets, self.phy_to_link_packets)
        self.usb_driver_proc = self.usb_driver.proc()
        return UlpiAgent.getDrivers(self)

    def monitor(self):
        self.run_usb_driver()
        yield from UlpiAgent.monitor(self)
        self.run_usb_driver()

    def getMonitors(self):
        # link/device
        assert self.descriptors is not None
        self.usb_driver = UlpiUsbDevProcAgent(self.phy_to_link_packets,
                                              self.link_to_phy_packets,
                                              self.descriptors)
        self.usb_driver_proc = self.usb_driver.proc()

        return UlpiAgent.getMonitors(self)

