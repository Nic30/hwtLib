from collections import deque

from hwt.hdl.constants import NOP
from hwt.simulator.agentBase import SyncAgentBase
from hwtLib.peripheral.usb.usb2.ulpi import ulpi_reg_otg_control_t_reset_defaults, \
    ulpi_reg_function_control_t_reset_default
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b_rx, Utmi_8b, utmi_interrupt_t
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.triggers import WaitCombStable, WaitCombRead, WaitWriteOnly
from pyMathBitPrecise.bit_utils import ValidityError
from hwtLib.peripheral.usb.constants import USB_LINE_STATE


class Utmi_8b_rxAgent(SyncAgentBase):
    """
    Simulation agent for :class:`hwtLib.peripheral.usb.usb2.utmi.Utmi_8b_rx` interface.

    :attention: "active" signal acts as a valid, "valid" signal acts as a mask
    :ivar data: Deque[Deque[Tuple[int, int]]] (internal deque represents packets, tuple represents data, error)

    .. figure:: ./_static/utmi_rx.png
    """
    USB_ERROR = "ERROR"

    def __init__(self, sim:HdlSimulator, intf: Utmi_8b_rx, allowNoReset=False):
        SyncAgentBase.__init__(self, sim, intf, allowNoReset=allowNoReset)
        self._last_active = 0
        self.data = deque()
        self.actual_packet = None

    def get_data(self):
        i = self.intf
        if i.error.read():
            d = self.USB_ERROR
        else:
            d = int(i.data.read())
        return d

    def set_active(self, val):
        self.intf.active.write(val)
        self._last_active = val

    def set_data(self, data):
        if data is None:
            d = None
            e = None
        else:
            if data is self.USB_ERROR:
                e = 1
                d = None
            else:
                e = 0
                d = data

        i = self.intf
        i.data.write(d)
        i.error.write(e)

    def monitor(self):
        yield WaitCombStable()
        if self.notReset():
            intf = self.intf
            active = int(intf.active.read())
            if active:
                if not self._last_active:
                    # start of packet
                    assert self.actual_packet is None
                    self.actual_packet = deque()

                vld = int(intf.valid.read())
                if vld:
                    d = self.get_data()
                    if self._debugOutput is not None:
                        self._debugOutput.write("%s, read, %d: %r\n" % (
                            intf._getFullName(),
                            self.sim.now, d))
                    self.actual_packet.append(d)

            elif self._last_active:
                # end of packet
                assert self.actual_packet, (self.sim.now, intf._getFullName())
                self.data.append(self.actual_packet)
                self.actual_packet = None

            self._last_active = active

    def driver(self):
        yield WaitCombRead()
        d = NOP
        active = 0
        if self.notReset():
            if self.actual_packet:
                d = self.actual_packet.popleft()
                active = 1
            elif self._last_active == 1:
                # end of packet, need to have at least one clk tick with active=0
                active = 0
                d = NOP

            elif self.data and self._last_active == 0:
                self.actual_packet = self.data.popleft()
                # first beat of packet (active=1, valid=0)
                active = 1
                d = NOP

        yield WaitWriteOnly()
        intf = self.intf
        if d is NOP:
            self.set_data(None)
            intf.valid.write(0)
        else:
            self.set_data(d)
            intf.valid.write(1)

        self.set_active(active)
        if active and self._debugOutput is not None:
            self._debugOutput.write("%s, wrote, %d: %r\n" % (
                intf._getFullName(),
                self.sim.now, self.actualData))


class Utmi_8b_txAgent(SyncAgentBase):
    """
    Simulation agent for :class:`hwtLib.peripheral.usb.usb2.utmi.Utmi_8b_tx` interface.

    :ivar data: Deque[Deque[int]] (internal deque represents packets)

    .. figure:: ./_static/utmi_rx.png
    """

    def __init__(self, sim:HdlSimulator, intf, allowNoReset=False,
        wrap_monitor_and_driver_in_edge_callback=True):
        SyncAgentBase.__init__(
            self, sim, intf, allowNoReset=allowNoReset,
            wrap_monitor_and_driver_in_edge_callback=wrap_monitor_and_driver_in_edge_callback)
        self.data = deque()
        self.actual_packet = None
        self._last_ready = 0
        self._last_valid = 0

    def driver(self):
        yield WaitCombRead()
        if self.notReset():
            d = NOP
            if self.actual_packet:
                d = self.actual_packet[0]
            elif self._last_valid == 1:
                # end of packet, need to have at least one clk tick with active=0
                d = NOP
                self.actual_packet = None

            elif self.data and self._last_ready == 0:
                self.actual_packet = self.data.popleft()
                # first beat of packet (active=1, valid=0)
                d = self.actual_packet[0]

            yield WaitWriteOnly()
            intf = self.intf

            if d is NOP:
                intf.data.write(None)
                intf.vld.write(0)
            else:
                intf.data.write(d)
                intf.vld.write(1)

            yield WaitCombStable()

            try:
                rd = int(intf.rd.read())
            except ValidityError:
                raise AssertionError(self.sim.now, intf._getFullName(), "invalid rd (would cause desynchronization of the channel)")

            if d is NOP:
                if self._last_valid == 1:
                    assert rd == 1, (self.sim.now, intf._getFullName(), rd, "Ready must be 1 or 1 clk tick after end of packet (EOP state)")

            if rd and self.actual_packet:
                self.actual_packet.popleft()

        else:
            rd = 0
            d = NOP

        self._last_ready = rd
        self._last_valid = int(d is not NOP)

    def monitor(self):
        yield WaitCombRead()
        if self.notReset():
            yield WaitWriteOnly()
            yield WaitCombRead()
            intf = self.intf
            try:
                vld = int(intf.vld.read())
            except ValidityError:
                    raise AssertionError(self.sim.now, intf._getFullName(), "invalid vld, this would case desynchronization")
            if self._last_valid and not vld:
                # end of packet
                self.data.append(self.actual_packet)
                self.actual_packet = None
            elif not self._last_valid and vld:
                # start of packet
                self.actual_packet = deque()

            if vld:
                try:
                    d = int(intf.data.read())
                except ValidityError:
                    raise AssertionError(self.sim.now, intf._getFullName(), "invalid data")
                self.actual_packet.append(d)

            if vld or self._last_valid:
                rd = 1
            else:
                rd = 0

            yield WaitWriteOnly()
            intf.rd.write(rd)

            self._last_ready = rd
            self._last_valid = vld

        else:
            self._last_ready = 0
            self._last_valid = 0


class Utmi_8bAgent(AgentBase):
    """
    Simulation agent for :class:`hwtLib.peripheral.usb.usb2.utmi.Utmi_8b` interface.
    """

    def __init__(self, sim:HdlSimulator, intf: Utmi_8b):
        AgentBase.__init__(self, sim, intf)
        for i in [intf.function_control, intf.otg_control, intf.interrupt, intf.rx, intf.tx]:
            i._initSimAgent(sim)

    @property
    def link_to_phy_packets(self):
        return self.intf.tx._ag.data

    @link_to_phy_packets.setter
    def link_to_phy_packets_setter(self, v):
        self.intf.tx._ag.data = v

    @property
    def actual_link_to_phy_packet(self):
        return self.intf.tx._ag.actual_packet

    @actual_link_to_phy_packet.setter
    def actual_link_to_phy_packet_setter(self, v):
        self.intf.tx._ag.actual_packet = v

    @property
    def phy_to_link_packets(self):
        return self.intf.rx._ag.data

    @phy_to_link_packets.setter
    def phy_to_link_packets_setter(self, v):
        self.intf.rx._ag.data = v

    @property
    def actual_phy_to_link_packet(self):
        return self.intf.tx._ag.actual_packet

    @actual_phy_to_link_packet.setter
    def actual_phy_to_link_packet_setter(self, v):
        self.intf.rx._ag.actual_packet = v

    def getMonitors(self):
        return [
           *self.intf.tx._ag.getDrivers(),
           *self.intf.rx._ag.getMonitors(),
           self.monitor(),
        ]

    def monitor(self):
        yield WaitWriteOnly()
        intf = self.intf
        for i in intf.function_control._interfaces:
            d = ulpi_reg_function_control_t_reset_default[i._name]
            i.write(d)

        for i in intf.otg_control._interfaces:
            d = ulpi_reg_otg_control_t_reset_defaults[i._name]
            i.write(d)
        intf.tx.vld.write(0)

    def getDrivers(self):
        return [
           *self.intf.tx._ag.getMonitors(),
           *self.intf.rx._ag.getDrivers(),
           self.driver(),
        ]

    def driver(self):
        yield WaitWriteOnly()
        intf = self.intf
        intf.LineState.write(USB_LINE_STATE.J)
        intf.interrupt._ag.set_data(tuple(0 for _ in range(len(utmi_interrupt_t.fields) - 1)))
        intf.tx.rd.write(0)
        intf.rx.valid.write(0)
        intf.rx.active.write(0)

