from typing import Deque, Union

from hwtLib.peripheral.usb.sim.agent_base import UsbPacketToken, UsbPacketData, \
    UsbPacketHandshake
from hwtLib.peripheral.usb.sim.usb_agent_device import UsbDevAgent
from hwtLib.peripheral.usb.usb2.ulpi import ULPI_TX_CMD, Ulpi
from hwtLib.peripheral.usb.usb2.ulpi_agent import UlpiAgent
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbHostProcAgent
from hwtSimApi.hdlSimulator import HdlSimulator


class UlpiUsbHostProcAgent(UtmiUsbHostProcAgent):
    """
    A simulation agent for :class:`hwtLib.peripheral.usb.usb2.ulpi.Ulpi` interface
    with the functionality of the host.
    """

    def parse_packet(self, p: Deque[int]):
        # need to cut of ulpi tx_cmd header
        tx_cmd = p.popleft()
        if ULPI_TX_CMD.is_USB_PID(tx_cmd):
            pid = ULPI_TX_CMD.get_USB_PID(tx_cmd)
            return self.parse_packet_pid_and_bytes(pid, p)
        else:
            raise NotImplementedError(tx_cmd)

    def deparse_packet(self, p: Union[UsbPacketToken, UsbPacketData, UsbPacketHandshake]):
        cls = type(p)
        v = UtmiUsbHostProcAgent.deparse_packet(self, p)
        v[0] = ULPI_TX_CMD.USB_PID(p.pid)
        return v


class UlpiUsbDevProcAgent(UsbDevAgent):

    def parse_packet_pid_and_bytes(self, pid: int, p: Deque[int]):
        return UlpiUsbHostProcAgent.parse_packet_pid_and_bytes(self, pid, p)

    def parse_packet(self, p: Deque[int]):
        return UlpiUsbHostProcAgent.parse_packet(self, p)

    def deparse_packet(self, p: Union[UsbPacketToken, UsbPacketData, UsbPacketHandshake]):
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

