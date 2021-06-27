from collections  import deque
from typing import Deque, Union

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.simulator.agentBase import SyncAgentBase
from hwtLib.peripheral.usb.constants import usb_addr_t, usb_endp_t, \
    usb_crc5_t, usb_pid_t, USB_PID
from hwtLib.peripheral.usb.sim.agent_base import UsbPacketToken, UsbPacketData, \
    UsbPacketHandshake
from hwtLib.peripheral.usb.sim.usb_agent_device import UsbDevAgent
from hwtLib.peripheral.usb.sim.usb_agent_host import UsbHostAgent
from hwtLib.peripheral.usb.usb2.utmi_agent import Utmi_8bAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.process_utils import CallbackLoop


class UtmiUsbHostProcAgent(UsbHostAgent):
    """
    A simulation agent for :class:`hwtLib.peripheral.usb.usb2.utmi.Utmi_8b` interface
    with the functionality of the host.
    """
    usb_packet_token_t = HStruct(
        (usb_pid_t, "pid"),
        (usb_pid_t, "pid_inv"),  # inversion of the pid
        (usb_addr_t, "addr"),
        (usb_endp_t, "endp"),
        (usb_crc5_t, "crc5"),  # :note: does not involve USB_PID, only addr, endp
    )

    def parse_packet_pid_and_bytes(self, pid: int, p: Deque[int]):
        if USB_PID.is_token(pid):
            return UsbPacketToken.from_pid_and_body_bytes(pid, p)
        elif USB_PID.is_data(pid):
            crc16_h = p.pop()
            crc16_l = p.pop()
            crc16 = (crc16_h << 8 | crc16_l)
            new_p = UsbPacketData(pid, p)
            expected_crc = new_p.crc16()
            assert crc16 == expected_crc, (crc16, expected_crc, p)
            return new_p
        elif USB_PID.is_hs(pid):
            return UsbPacketHandshake(pid)
        else:
            raise NotImplementedError(pid)

    def parse_packet(self, p: Deque[int]):
        # need to cut of ulpi tx_cmd header
        pid = int(p.popleft())
        pid_inv = (pid & 0xf0) >> 4
        pid &= 0xf
        assert pid == (~pid_inv & 0xf), (pid, pid_inv)
        return self.parse_packet_pid_and_bytes(pid, p)

    def deparse_packet(self, p: Union[UsbPacketToken, UsbPacketData, UsbPacketHandshake]):
        cls = type(p)
        v = deque()
        if cls is UsbPacketToken:
            v0 = self.usb_packet_token_t.from_py({
                "pid": p.pid,
                "pid_inv":~p.pid & 0xf,
                "addr": p.addr,
                "endp": p.endp,
                "crc5": p.crc5(),
            })
            v1 = v0._reinterpret_cast(Bits(8)[self.usb_packet_token_t.bit_length() // 8])
            v.extend(int(_v) for _v in v1)

        elif cls is UsbPacketData:
            v.append(((~p.pid & 0xf) << 4) | p.pid)
            v.extend(p.data)
            crc16 = p.crc16()
            v.append(crc16 & 0xff)
            v.append(crc16 >> 8)

        elif cls is UsbPacketHandshake:
            v.append(((~p.pid & 0xf) << 4) | p.pid)

        else:
            raise NotImplementedError(cls, p)
        return v


class UtmiUsbDevProcAgent(UsbDevAgent):

    def parse_packet_pid_and_bytes(self, pid: int, p: Deque[int]):
        return UtmiUsbHostProcAgent.parse_packet_pid_and_bytes(self, pid, p)

    def parse_packet(self, p):
        return UtmiUsbHostProcAgent.parse_packet(self, p)

    def deparse_packet(self, p):
        # need to add ulpi tx_cmd header
        return UtmiUsbHostProcAgent.deparse_packet(self, p)


class UtmiUsbAgent(Utmi_8bAgent, SyncAgentBase):
    """
    :class:` hwtLib.peripheral.usb.usb2.utmi_agent.Utmi_8bAgent`
    with device host logic and USB stack
    """

    def __init__(self, sim:HdlSimulator, intf:Utmi_8bAgent, allowNoReset=False,
                 wrap_monitor_and_driver_in_edge_callback=True):
        Utmi_8bAgent.__init__(self, sim, intf)
        self.descriptors = None
        self.usb_driver = None
        self.usb_driver_proc = None
        self.clk = self.intf._getAssociatedClk()
        self.rst = self._discoverReset(intf, allowNoReset)
        self.monitor = CallbackLoop(sim, self.clk, self.monitor, self.getEnable)
        self.driver = CallbackLoop(sim, self.clk, self.driver, self.getEnable)

    def run_usb_driver(self):
        if self.usb_driver_proc is not None:
            try:
                next(self.usb_driver_proc)
            except StopIteration:
                pass

    def driver_init(self):
        yield from Utmi_8bAgent.driver(self)

    def driver(self):
        self.run_usb_driver()

    def getDrivers(self):
        # PHY/host
        if self.usb_driver is None:
            self.usb_driver = UtmiUsbHostProcAgent(self.link_to_phy_packets,
                                                   self.phy_to_link_packets)
        self.usb_driver_proc = self.usb_driver.proc()
        return [
            self.driver_init(),
            *Utmi_8bAgent.getDrivers(self)
        ]

    def monitor_init(self):
        yield from Utmi_8bAgent.monitor(self)

    def monitor(self):
        self.run_usb_driver()

    def getMonitors(self):
        # link/device
        assert self.descriptors is not None
        if self.usb_driver is None:
            self.usb_driver = UtmiUsbDevProcAgent(self.phy_to_link_packets,
                                                  self.link_to_phy_packets,
                                                  self.descriptors)
        self.usb_driver_proc = self.usb_driver.proc()
        return [
            self.monitor_init(),
            *Utmi_8bAgent.getMonitors(self)
        ]

